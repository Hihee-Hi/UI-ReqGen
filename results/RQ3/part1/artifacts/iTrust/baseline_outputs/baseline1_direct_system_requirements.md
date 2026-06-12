# iTrust - Baseline 1 (Direct LLM Summarization)

## SR-01 — User Authentication and Role-Based Access
The system must authenticate users based on their credentials and assign them roles such as patient, healthcare provider, administrator, or public health authority. Each role should have access to specific functionalities tailored to their responsibilities, ensuring secure and appropriate access to sensitive healthcare data.

**Source files:**
- authenticate.txt
- login.txt
- global.txt

## SR-02 — Personnel and Patient Management
Administrators and healthcare providers must be able to add, edit, and manage personnel and patient records, including demographic information, medical IDs, and secure credentials. This functionality ensures efficient onboarding and management of healthcare personnel and patients while maintaining data security.

**Source files:**
- auth_admin_addER.txt
- auth_admin_addHCP.txt
- auth_admin_addPHA.txt
- auth_hcp-uap_addPatient.txt

## SR-03 — Appointment Scheduling and Management
The system should allow healthcare providers and administrators to schedule, view, and manage appointments, including setting reminders for patients. This functionality helps maintain efficient scheduling and reduces missed appointments, enhancing patient care and operational efficiency.

**Source files:**
- auth_admin_editApptType.txt
- auth_hcp_scheduleAppt.txt
- auth_hcp_viewAppt.txt

## SR-04 — Healthcare Data Management and Reporting
Healthcare providers must be able to document office visits, manage patient health records, and generate comprehensive reports. This includes updating lab procedures, prescriptions, and chronic disease risk assessments, ensuring accurate and up-to-date patient information for effective healthcare delivery.

**Source files:**
- auth_hcp-uap_documentOfficeVisit.txt
- auth_hcp-uap_editBasicHealth.txt
- auth_hcp-uap_editOfficeVisit.txt
- auth_hcp-uap_viewMyReportRequests.txt

## SR-05 — Secure Messaging and Communication
The system should facilitate secure communication between patients and healthcare providers through messaging features, allowing users to send, receive, and reply to messages. This ensures timely and organized exchanges of information, supporting effective patient-provider interactions.

**Source files:**
- auth_hcp_messageInbox.txt
- auth_hcp_messageOutbox.txt
- auth_patient_messageInbox.txt
- auth_patient_messageOutbox.txt

## SR-06 — Telemedicine and Remote Monitoring
The system must support telemedicine functionalities, allowing patients and healthcare providers to report and monitor health data remotely. This includes tracking physiological metrics like blood pressure and glucose levels, ensuring continuous patient care and timely interventions.

**Source files:**
- auth_patient_addTelemedicineData.txt
- auth_uap_addTelemedicineData.txt
- auth_hcp_monitorPatients.txt

## SR-07 — Adverse Event Monitoring and Public Health Management
Public health administrators should be able to monitor and analyze adverse events related to medications and immunizations. The system must provide tools for tracking trends, generating reports, and facilitating timely public health interventions to ensure patient safety.

**Source files:**
- auth_pha_monitorAdverseEvents.txt
- auth_pha_adverseEventChart.txt
- auth_pha_adverseEventDetails.txt

## SR-08 — User Profile and Information Management
Users should be able to view and update their personal information, including demographic details and security settings. This functionality ensures that user profiles are accurate and secure, supporting personalized interactions within the healthcare system.

**Source files:**
- auth_patient_editMyDemographics.txt
- auth_staff_editMyDemographics.txt
- auth_hcp_information.txt

## SR-09 — System Error Handling and Security
The system must provide robust error handling and security measures, including session management, access restrictions, and error notifications. This ensures the integrity and reliability of the system, protecting sensitive healthcare data from unauthorized access.

**Source files:**
- errors_noaccess.txt
- errors_badredirect.txt
- errors_nodb.txt
