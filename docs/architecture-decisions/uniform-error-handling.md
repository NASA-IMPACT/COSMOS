# Uniform Error Handling

## Status
Proposed

## Context
The current error handling system logs errors only in the terminal, which are neither preserved nor useful for developers or users. This approach fails to inform users of encountered issues and does not support debugging by developers. A consistent and efficient error-handling strategy is required to enhance user experience and simplify debugging.

## Decision
The **Error Dashboard** approach is proposed to be adopted as the method for handling system errors. This decision aligns with the need to consolidate real-time and asynchronous errors in a centralized location for better tracking and resolution.

### Why This Decision Was Taken
Since there are tasks that run asynchronously (e.g., Celery tasks), errors from these operations cannot be shown to the user in real-time. To ensure that both real-time and asynchronous errors are recorded and displayed, this approach was chosen.

- **Real-Time Errors**: These will be updated in the notification dashboard immediately as they occur.
- **Asynchronous Errors**: Errors encountered during asynchronous tasks (e.g., Celery tasks) will be recorded and updated in the dashboard once the task completes. 

To achieve this, a targeted script will be developed to monitor asynchronous tasks. Details of this script are outlined in the **Monitoring Asynchronous Tasks** section of this ADR.

## Consequences

### Positive
- **Centralization**: All errors are consolidated in one place, reducing the chances of overlooked issues.
- **Improved User Experience**: Users have a clear view of errors affecting their operations without relying on backend logs or email notifications.
- **Scalability**: Suitable for large-scale operations involving asynchronous and real-time tasks.

### Negative
- **Navigation Overhead**: Users must navigate to the dashboard, which could be less convenient than inline error notifications.
- **Resource Requirements**: Developing and maintaining the dashboard requires additional frontend and backend resources.

## Alternatives Considered

### 1. **Logging System**
- **Approach**: Use Python’s built-in logging library to save structured logs with details like timestamps and severity levels.
- **Advantages**:
  - Preserves logs for debugging.
  - Differentiates critical and minor errors for better prioritization.
  - Efficient for monitoring asynchronous tasks.
- **Disadvantage**:
  - Primarily benefits developers; does not directly improve user interaction.

### 2. **Frontend Notifications**
- **Approach**: Display error messages directly on the frontend.
- **Advantages**:
  - Enhances user interaction by providing immediate feedback.
- **Disadvantages**:
  - Resource-intensive to implement.
  - Real-time feedback is challenging for asynchronous tasks.

### 3. **Email Notifications**
- **Approach**: Send email alerts for critical failures.
- **Advantages**:
  - Simple to implement.
  - Suitable for asynchronous task monitoring.
- **Disadvantage**:
  - Users need to register their emails.
  - Requires users to check emails, reducing immediacy of feedback.

### 4. **Error Dashboard**
- **Approach**: Display errors on a dedicated frontend dashboard.
- **Advantages**:
  - Consolidates both real-time and asynchronous errors.
  - Provides a centralized location for error tracking.
- **Disadvantages**:
  - Requires navigation away from the operational page to view errors.

## Monitoring Asynchronous Tasks
A targeted script will be developed to monitor asynchronous tasks for errors during import operations:
- **Trigger**: Activated at the start of an import operation.
- **Duration**: Runs for 10 minutes, polling the Flower API every minute.
- **Functionality**:
  - Detects failed tasks related to the import.
  - Notifies developers or users as appropriate.

## References
- Issue: [#1112](#)
