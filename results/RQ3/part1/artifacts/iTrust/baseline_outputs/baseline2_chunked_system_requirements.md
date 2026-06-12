# iTrust - Baseline 2 (Naive Chunk-based Summarization)

## SR-01 — Personnel Management and Account Creation
Administrators can add new personnel, including Emergency Responders, Healthcare Providers, and Public Health Administrators, by entering their basic information. The system generates a unique Medical ID and temporary password for each new account, ensuring secure onboarding and accurate user identification.

**Source files:**
- auth_admin_addER.txt
- auth_admin_addHCP.txt
- auth_admin_addPHA.txt
- util_getUser.txt

## SR-02 — Appointment and Scheduling Management
Administrators can manage appointment types to meet clinic scheduling requirements, while healthcare providers can schedule appointments, view their calendar, and manage patient visit reminders. This optimizes patient care and ensures efficient scheduling practices.

**Source files:**
- auth_admin_editApptType.txt
- auth_hcp_scheduleAppt.txt
- auth_hcp_calendar.txt
- auth_hcp_visitReminders.txt

## SR-03 — Code Management for Billing and Documentation
Administrators can manage medical codes such as CPT, ICD, LOINC, and NDC, including adding, updating, and validating them. This functionality ensures accurate billing and documentation practices within the healthcare system.

**Source files:**
- auth_admin_editCPTProcedureCodes.txt
- auth_admin_editICDCodes.txt
- auth_admin_editLOINCCodes.txt
- auth_admin_editNDCodes.txt

## SR-04 — Communication and Messaging
The system provides messaging functionalities for administrators, healthcare providers, and patients, including sending, receiving, and organizing messages. This ensures efficient communication within the healthcare environment.

**Source files:**
- auth_admin_remindersMessageOutbox.txt
- auth_hcp_messageInbox.txt
- auth_hcp_messageOutbox.txt
- auth_patient_messageInbox.txt
- auth_patient_messageOutbox.txt

## SR-05 — Patient Health Record Management
Healthcare providers can manage and update patient health records, including basic health data, office visit documentation, and prescription information. Patients can view their medical records and manage their health data, ensuring transparency and accessibility.

**Source files:**
- auth_hcp-uap_editBasicHealth.txt
- auth_hcp-uap_documentOfficeVisit.txt
- auth_patient_viewMyRecords.txt
- auth_patient_viewOfficeVisit.txt

## SR-06 — Adverse Event Monitoring and Reporting
Public Health Administrators can monitor and analyze adverse events related to prescriptions and immunizations using visual tools to track trends. This functionality ensures public health safety and proactive event management.

**Source files:**
- auth_pha_adverseEventChart.txt
- auth_pha_adverseEventDetails.txt
- auth_pha_monitorAdverseEvents.txt

## SR-07 — User Authentication and Session Management
The system ensures secure user authentication, session management, and access control, protecting sensitive information and maintaining system integrity. It includes password reset processes and error handling for incorrect inputs.

**Source files:**
- authenticate.txt
- global.txt
- login.txt
- logout.txt
- util_resetPassword.txt

## SR-08 — Dynamic User Interaction Frame
A feature that provides a movable frame within a web page to display additional user-related content or features dynamically, enhancing user interaction without disrupting the main workflow.

**Source files:**
- util_getUserFrame.txt

## SR-09 — System Transaction Logging
A logging tool that records all system transactions with details such as date, transaction ID, type, and user IDs involved. This aids in troubleshooting, auditing, and testing system operations.

**Source files:**
- util_transactionLog.txt
