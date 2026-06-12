# Dronology - Baseline 1 (Direct LLM Summarization)

## SR-01 — Comprehensive Drone Monitoring and Control Interface
The system provides a unified interface for users to monitor and control active drone flights. Users can view real-time status, health, and battery life of drones, and manage their operations through a centralized control panel. This interface supports situational awareness by displaying essential information and allowing users to focus on specific drones or view all active drones simultaneously.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_AFControlsComponent.txt
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_AFInfoPanel.txt
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_UAVStatusWrapper.txt

## SR-02 — Dynamic Flight Route Management
Users can create, edit, and manage flight routes for drones using an interactive map interface. The system allows for the addition and modification of waypoints, including setting specific altitudes and speeds. Users can preview routes, make adjustments, and ensure routes are complete before assignment. The interface supports drag-and-drop functionality for reordering routes and provides confirmation prompts to prevent accidental changes.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_flightroutes_FRMainLayout.txt
- src_main_java_edu_nd_dronology_ui_vaadin_flightroutes_FRInfoBox.txt
- src_main_java_edu_nd_dronology_ui_vaadin_flightroutes_FRMapComponent.txt

## SR-03 — Emergency Response Capabilities
In emergency situations, users can quickly command drones to hover in place or return to their home base. The system allows for global actions affecting multiple drones simultaneously, ensuring a rapid and comprehensive response. This functionality is crucial for maintaining safety and control during unexpected events.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_AFEmergencyComponent.txt
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_AFInfoBox.txt

## SR-04 — Mission Execution and Management
The system enables users to upload, execute, and manage drone missions efficiently. Users can initiate missions with a single command and have the ability to cancel them if necessary. This feature ensures that drone operations can be adapted to real-time requirements, providing flexibility in mission management.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_AFMissionOperations.txt
- src_main_java_edu_nd_dronology_ui_vaadin_activeflights_MissionHandler.txt

## SR-05 — Interactive Map and Visualization Tools
Users have access to a dynamic map interface that displays real-time drone locations and flight paths. The map supports various views and layers, allowing users to switch between different geographical perspectives. This feature enhances situational awareness and aids in navigation and analysis by providing detailed visual information.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_map_LeafletmapFactory.txt
- src_main_java_edu_nd_dronology_ui_vaadin_map_VaadinUIMapConstants.txt

## SR-06 — User Notifications and Alerts
The system provides a notification feature to alert users of important updates or actions required. Notifications are prominently displayed to ensure they capture user attention, allowing for timely responses to critical information. This feature supports effective communication and decision-making during drone operations.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_utils_DronologyNotification.txt

## SR-07 — Customizable User Settings
Users can customize system settings, including map appearance, refresh rates, and project names. These configurations are saved for future sessions, ensuring a personalized and consistent user experience. Default settings are applied if initial configurations are missing, allowing users to start with a pre-configured environment.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_utils_Configuration.txt

## SR-08 — Efficient Navigation and Workflow Management
The system features a navigation bar that allows users to switch between active flights and flight routes seamlessly. This facilitates efficient workflow management by enabling users to transition smoothly between monitoring live drone activity and managing planned routes, ensuring a streamlined operational experience.

**Source files:**
- src_main_java_edu_nd_dronology_ui_vaadin_start_NavigationBar.txt
