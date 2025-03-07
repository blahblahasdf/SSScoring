# See: https://github.com/pr3d4t0r/SSScoring/blob/master/LICENSE.txt

"""
Streamlit-based application.

Issue deploying to Streamlit.io:
https://discuss.streamlit.io/t/pythonpath-issue-modulenotfounderror-in-same-package-where-app-is-defined/91170
"""

from ssscoring import __VERSION__
from ssscoring.appcommon import DZ_DIRECTORY
from ssscoring.appcommon import displayJumpDataIn
from ssscoring.appcommon import initDropZonesFromResource
from ssscoring.appcommon import initFileUploaderState
from ssscoring.appcommon import interpretJumpResult
from ssscoring.appcommon import isStreamlitHostedApp
from ssscoring.appcommon import plotJumpResult
from ssscoring.calc import convertFlySight2SSScoring
from ssscoring.calc import getFlySightDataFromCSVBuffer
from ssscoring.calc import processJump
from ssscoring.datatypes import JumpStatus
from ssscoring.mapview import speedJumpTrajectory
from ssscoring.units import UnitSystem, format_value_with_unit, meters_to_feet, kmh_to_mph

import pandas as pd
import streamlit as st

# Initialize session state for unit system if not exists
if 'unit_system' not in st.session_state:
    st.session_state.unit_system = UnitSystem.MIXED

# *** implementation ***

def _selectDZState(*args, **kwargs):
    if st.session_state.elevation:
        st.session_state.uploaderKey += 1
        st.session_state.trackFile = None


def _setSideBarAndMain():
    dropZones = initDropZonesFromResource(DZ_DIRECTORY)
    st.sidebar.title('1️⃣  SSScore %s β' % __VERSION__)
    st.session_state.processBadJump = st.sidebar.checkbox('Process bad jump', value=True, help='Display results from invalid jumps')
    dropZone = st.sidebar.selectbox('Select drop zone:', dropZones.dropZone, index=None, on_change=_selectDZState)
    if dropZone:
        st.session_state.elevation = dropZones[dropZones.dropZone == dropZone ].iloc[0].elevation
    else:
        st.session_state.elevation = None
        st.session_state.trackFile = None
    # Add unit system selector
    st.sidebar.selectbox(
        'Unit System',
        [system.value for system in UnitSystem],
        index=[system.value for system in UnitSystem].index(st.session_state.unit_system.value),
        key='unit_system_selector',
        help='Choose how measurements are displayed'
    )
    st.session_state.unit_system = UnitSystem(st.session_state.unit_system_selector)

    # Display elevation in selected unit system
    elevation = 0.0 if st.session_state.elevation is None else st.session_state.elevation
    elevation_str = format_value_with_unit(elevation, st.session_state.unit_system, "altitude")
    st.sidebar.metric('Elevation', value=elevation_str)
    trackFile = st.sidebar.file_uploader('Track file', [ 'CSV' ], disabled=st.session_state.elevation == None, key = st.session_state.uploaderKey)
    if trackFile:
        st.session_state.trackFile = trackFile
    st.sidebar.button('Clear', on_click=_selectDZState)
    st.sidebar.link_button('Report missing DZ', 'https://github.com/pr3d4t0r/SSScoring/issues/new?template=report-missing-dz.md', icon=':material/breaking_news_alt_1:')
    st.sidebar.link_button('Feature request or bug report', 'https://github.com/pr3d4t0r/SSScoring/issues/new?template=Blank+issue', icon=':material/breaking_news_alt_1:')


def _getJumpDataFrom(trackFileBuffer: str) -> pd.DataFrame:
    dropZoneAltMSLMeters = 0.0 if st.session_state.elevation == None else st.session_state.elevation
    data = None
    tag = None
    if dropZoneAltMSLMeters is not None:
        rawData, tag = getFlySightDataFromCSVBuffer(trackFileBuffer, st.session_state.trackFile.name)
        data = convertFlySight2SSScoring(rawData, altitudeDZMeters=dropZoneAltMSLMeters)
    return data, tag


def _displayAllJumpDataIn(data: pd.DataFrame):
    # Create a copy of the dataframe to avoid modifying the original
    display_data = data.copy()
    
    # Convert units based on selected unit system
    if st.session_state.unit_system != UnitSystem.SI:
        # Convert altitude columns if not in SI
        altitude_cols = ['altitudeMSL', 'altitudeAGL']
        for col in altitude_cols:
            if col in display_data.columns:
                display_data[col] = display_data[col].apply(lambda x: meters_to_feet(x))
                
        # Convert speed columns if not in SI
        speed_cols = ['speedVertical', 'speedHorizontal', 'speed3D']
        for col in speed_cols:
            if col in display_data.columns:
                display_data[col] = display_data[col].apply(lambda x: kmh_to_mph(x))

    columns = ['plotTime'] + [column for column in display_data.columns if column != 'plotTime' and column != 'timeUnix']
    
    # Configure column units in headers
    unit_suffixes = {
        'altitudeMSL': ' (ft)' if st.session_state.unit_system != UnitSystem.SI else ' (m)',
        'altitudeAGL': ' (ft)' if st.session_state.unit_system != UnitSystem.SI else ' (m)',
        'speedVertical': ' (mph)' if st.session_state.unit_system != UnitSystem.SI else ' (km/h)',
        'speedHorizontal': ' (mph)' if st.session_state.unit_system != UnitSystem.SI else ' (km/h)',
        'speed3D': ' (mph)' if st.session_state.unit_system != UnitSystem.SI else ' (km/h)',
    }
    
    column_config = {
        'plotTime': st.column_config.NumberColumn(format='%.02f'),
        'speedAngle': st.column_config.NumberColumn(format='%.02f'),
        'speedAccuracyISC': st.column_config.NumberColumn(format='%.02f'),
    }
    
    # Add unit suffixes to column headers and format configuration
    for col in columns:
        if col in unit_suffixes:
            column_config[col] = st.column_config.NumberColumn(
                label=f"{col}{unit_suffixes[col]}",
                format='%.02f'
            )
    
    st.html('<h3>All rows of jump data</h3>')
    st.dataframe(
        display_data,
        column_order=columns,
        column_config=column_config,
        hide_index=True
    )


def _displayScoresIn(rawData: dict):
    st.html('<h3>Scores</h3>')
    data = pd.DataFrame.from_dict({ 'time': rawData.values(), 'score': rawData.keys(), })
    data.time = data.time.apply(lambda x: '%.2f' % x)
    st.dataframe(data, hide_index=True)


def main():
    if not isStreamlitHostedApp():
        st.set_page_config(layout = 'wide')
    initFileUploaderState('trackFile')
    _setSideBarAndMain()

    col0, col1 = st.columns([ 0.4, 0.6, ])
    if st.session_state.trackFile:
        data, tag = _getJumpDataFrom(st.session_state.trackFile.getvalue())
        jumpResult = processJump(data)
        jumpStatusInfo, \
        scoringInfo, \
        badJumpLegend, \
        jumpStatus = interpretJumpResult(tag, jumpResult, st.session_state.processBadJump)
        with col0:
            st.html('<h3>'+jumpStatusInfo+scoringInfo+(badJumpLegend if badJumpLegend else '')+'</h3>')
        if jumpStatus == JumpStatus.OK:
            with col0:
                displayJumpDataIn(jumpResult.table)
                _displayAllJumpDataIn(jumpResult.data)
                _displayScoresIn(jumpResult.scores)
            with col1:
                st.write('Jump result = %s' % jumpStatus)
                plotJumpResult(tag, jumpResult)
                st.write('Brightest point corresponds to the max speed')
                st.pydeck_chart(speedJumpTrajectory(jumpResult))


if '__main__' == __name__:
    main()

