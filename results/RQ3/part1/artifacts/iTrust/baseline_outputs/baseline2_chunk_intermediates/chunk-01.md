# iTrust - chunk-01 local themes

## T-01 — Personnel Management and Account Creation
Administrators can add new personnel such as Emergency Responders, Healthcare Providers, and Public Health Administrators by entering their basic information. The system generates a unique Medical ID and temporary password for each new account, ensuring secure onboarding.

**Source files:**
- auth_admin_addER.txt
- auth_admin_addHCP.txt
- auth_admin_addPHA.txt

## T-02 — Appointment and Scheduling Management
Administrators can manage appointment types by adding or updating them, ensuring they meet clinic scheduling requirements. Healthcare providers can schedule appointments, view their calendar, and manage patient visit reminders to optimize patient care.

**Source files:**
- auth_admin_editApptType.txt
- auth_hcp_scheduleAppt.txt
- auth_hcp_calendar.txt
- auth_hcp_visitReminders.txt

## T-03 — Code Management for Billing and Documentation
Administrators can manage CPT, ICD, LOINC, and NDC codes, including adding, updating, and validating them. This ensures accurate billing and documentation practices within the healthcare system.

**Source files:**
- auth_admin_editCPTProcedureCodes.txt
- auth_admin_editICDCodes.txt
- auth_admin_editLOINCCodes.txt
- auth_admin_editNDCodes.txt

## T-04 — Communication and Messaging
The system provides messaging functionalities for administrators, healthcare providers, and patients, including sending, receiving, and organizing messages. This ensures efficient communication within the healthcare environment.

**Source files:**
- auth_admin_remindersMessageOutbox.txt
- auth_hcp_messageInbox.txt
- auth_hcp_messageOutbox.txt
- auth_patient_messageInbox.txt
- auth_patient_messageOutbox.txt

## T-05 — Patient Health Record Management
Healthcare providers can manage and update patient health records, including basic health data, office visit documentation, and prescription information. Patients can view their medical records and manage their health data.

**Source files:**
- auth_hcp-uap_editBasicHealth.txt
- auth_hcp-uap_documentOfficeVisit.txt
- auth_patient_viewMyRecords.txt
- auth_patient_viewOfficeVisit.txt

## T-06 — Adverse Event Monitoring and Reporting
Public Health Administrators can monitor and analyze adverse events related to prescriptions and immunizations, using visual tools to track trends and ensure public health safety.

**Source files:**
- auth_pha_adverseEventChart.txt
- auth_pha_adverseEventDetails.txt
- auth_pha_monitorAdverseEvents.txt

## T-07 — User Authentication and Session Management
The system ensures secure user authentication, session management, and access control, protecting sensitive information and maintaining system integrity.

**Source files:**
- authenticate.txt
- global.txt
- login.txt
- logout.txt
