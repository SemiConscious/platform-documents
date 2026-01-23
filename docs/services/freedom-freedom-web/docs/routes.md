# Application Routes

## Overview

This document provides comprehensive documentation of all application routes and views within the Freedom Web application. The routing system is designed to support a call center/telephony operations workflow, organizing functionality into logical sections for managing calls, voicemails, contacts, team collaboration, and system configuration.

Freedom Web utilizes a single-page application (SPA) architecture with client-side routing, enabling seamless navigation between views while maintaining CTI (Computer Telephony Integration) bridge connections and real-time call state.

---

## Route Overview

### Route Architecture

The Freedom Web application implements a hierarchical routing structure with the following characteristics:

- **Base Path**: All application routes are prefixed with the application context
- **Authentication**: Routes are protected by JWT-based authentication guards
- **Lazy Loading**: Feature modules are loaded on-demand to optimize initial load times
- **State Preservation**: Active call state is preserved across route transitions

### Route Map Summary

| Route Path | Component/View | Description | Auth Required |
|------------|---------------|-------------|---------------|
| `/` | Dashboard | Main landing page with overview widgets | Yes |
| `/active-calls` | ActiveCallsView | Real-time active call management | Yes |
| `/wrap-ups` | WrapUpsView | Post-call wrap-up and disposition | Yes |
| `/activities` | ActivitiesView | Activity tracking and history | Yes |
| `/call-logs` | CallLogsView | Historical call records | Yes |
| `/voicemails` | VoicemailsView | Voicemail inbox management | Yes |
| `/voicemail-drop` | VoicemailDropView | Pre-recorded voicemail messages | Yes |
| `/address-book` | AddressBookView | Contact management | Yes |
| `/teams` | TeamsView | Team collaboration hub | Yes |
| `/settings` | SettingsView | User and application settings | Yes |

---

## Home/Dashboard

### Route Definition

```javascript
// Route Configuration
{
  path: '/',
  name: 'Dashboard',
  component: () => import('@/views/Dashboard.vue'),
  meta: {
    requiresAuth: true,
    title: 'Dashboard - Freedom Web',
    icon: 'home'
  }
}
```

### Purpose

The Dashboard serves as the central hub for call center agents, providing:

- **Call Statistics Widget**: Real-time metrics including calls handled, average handle time, and wait times
- **Queue Status**: Current queue depths and estimated wait times
- **Agent Status**: Personal performance metrics and status controls
- **Quick Actions**: One-click access to frequently used features
- **Notifications Panel**: System alerts and team messages

### View Components

```typescript
// Dashboard component structure
interface DashboardState {
  callStats: CallStatistics;
  queueStatus: QueueMetrics[];
  agentStatus: AgentStatus;
  recentActivities: Activity[];
  notifications: Notification[];
}
```

### Navigation Behavior

- Default landing page after successful authentication
- Maintains real-time WebSocket connection for live updates
- Refreshes statistics on 30-second intervals
- Preserves widget layout preferences per user

---

## Active Calls

### Route Definition

```javascript
{
  path: '/active-calls',
  name: 'ActiveCalls',
  component: () => import('@/views/ActiveCalls.vue'),
  meta: {
    requiresAuth: true,
    title: 'Active Calls - Freedom Web',
    icon: 'phone',
    keepAlive: true
  }
}
```

### Purpose

The Active Calls view is the primary workspace for handling live telephone interactions:

- **Call Control Panel**: Answer, hold, transfer, conference, and disconnect controls
- **Caller Information**: CRM integration displaying customer details and history
- **Call Timer**: Duration tracking with wrap-up time indicators
- **Transfer Directory**: Quick access to transfer destinations
- **Notes Panel**: Real-time note-taking during calls

### Features

```typescript
// Active Call Management Interface
interface ActiveCallView {
  currentCalls: ActiveCall[];
  selectedCall: ActiveCall | null;
  transferDestinations: TransferTarget[];
  callControls: CallControlActions;
}

interface ActiveCall {
  callId: string;
  direction: 'inbound' | 'outbound';
  callerNumber: string;
  callerName: string;
  startTime: Date;
  status: CallStatus;
  queueName: string;
  holdDuration?: number;
}
```

### CTI Integration

This view maintains direct integration with the CTI bridge for:

- Real-time call state synchronization
- Softphone control events
- DTMF tone transmission
- Recording controls

---

## Wrap-ups

### Route Definition

```javascript
{
  path: '/wrap-ups',
  name: 'WrapUps',
  component: () => import('@/views/WrapUps.vue'),
  meta: {
    requiresAuth: true,
    title: 'Wrap-ups - Freedom Web',
    icon: 'clipboard-check'
  }
}
```

### Purpose

The Wrap-ups view facilitates post-call processing and disposition:

- **Disposition Selection**: Categorize call outcomes with predefined codes
- **Call Notes**: Document conversation details and follow-up items
- **Scheduling**: Set callbacks and follow-up reminders
- **Quality Tags**: Apply quality assurance markers
- **Time Tracking**: Monitor wrap-up duration against targets

### Workflow

```typescript
// Wrap-up workflow stages
enum WrapUpStage {
  DISPOSITION_SELECT = 'disposition',
  NOTES_ENTRY = 'notes',
  FOLLOW_UP = 'followup',
  CONFIRMATION = 'confirm'
}

interface WrapUpData {
  callId: string;
  dispositionCode: string;
  notes: string;
  followUpRequired: boolean;
  followUpDate?: Date;
  qualityTags: string[];
  wrapUpDuration: number;
}
```

### Best Practices

1. **Complete wrap-ups promptly**: Supervisors can monitor wrap-up times
2. **Use consistent disposition codes**: Enables accurate reporting
3. **Document actionable items**: Ensures follow-through on commitments
4. **Tag quality issues**: Supports training and improvement initiatives

---

## Activities

### Route Definition

```javascript
{
  path: '/activities',
  name: 'Activities',
  component: () => import('@/views/Activities.vue'),
  meta: {
    requiresAuth: true,
    title: 'Activities - Freedom Web',
    icon: 'activity'
  }
}
```

### Purpose

The Activities view provides comprehensive activity tracking and history:

- **Activity Timeline**: Chronological view of all agent actions
- **Filter Controls**: Filter by activity type, date range, or contact
- **Activity Details**: Drill-down into specific activity records
- **Export Functionality**: Download activity reports

### Activity Types

```typescript
// Supported activity types
type ActivityType = 
  | 'call_inbound'
  | 'call_outbound'
  | 'voicemail_received'
  | 'voicemail_left'
  | 'email_sent'
  | 'email_received'
  | 'note_created'
  | 'callback_scheduled'
  | 'transfer_completed'
  | 'status_change';

interface Activity {
  id: string;
  type: ActivityType;
  timestamp: Date;
  agentId: string;
  contactId?: string;
  details: Record<string, any>;
  duration?: number;
}
```

---

## Call Logs

### Route Definition

```javascript
{
  path: '/call-logs',
  name: 'CallLogs',
  component: () => import('@/views/CallLogs.vue'),
  meta: {
    requiresAuth: true,
    title: 'Call Logs - Freedom Web',
    icon: 'phone-log'
  }
}
```

### Purpose

The Call Logs view provides access to historical call records:

- **Search & Filter**: Find calls by number, date, duration, or disposition
- **Call Details**: View comprehensive call information including recordings
- **Playback Controls**: Listen to call recordings (if enabled)
- **Export Options**: Generate reports in CSV or PDF format
- **Pagination**: Navigate through large datasets efficiently

### Data Structure

```typescript
interface CallLogEntry {
  callId: string;
  direction: 'inbound' | 'outbound' | 'internal';
  callerNumber: string;
  calledNumber: string;
  startTime: Date;
  endTime: Date;
  duration: number;
  waitTime: number;
  holdTime: number;
  talkTime: number;
  disposition: string;
  agentId: string;
  queueId: string;
  recordingUrl?: string;
  notes: string;
}
```

### Query Parameters

The route supports deep linking with query parameters:

```
/call-logs?startDate=2024-01-01&endDate=2024-01-31&direction=inbound&page=1
```

---

## Voicemails

### Route Definition

```javascript
{
  path: '/voicemails',
  name: 'Voicemails',
  component: () => import('@/views/Voicemails.vue'),
  meta: {
    requiresAuth: true,
    title: 'Voicemails - Freedom Web',
    icon: 'voicemail'
  }
}
```

### Purpose

The Voicemails view manages incoming voicemail messages:

- **Inbox Management**: View, organize, and process voicemail messages
- **Playback Controls**: Listen to messages with speed and skip controls
- **Transcription**: View AI-generated transcriptions (if available)
- **Actions**: Return call, forward, archive, or delete messages
- **Status Tracking**: Mark messages as new, read, or urgent

### Features

```typescript
interface Voicemail {
  id: string;
  callerNumber: string;
  callerName: string;
  receivedAt: Date;
  duration: number;
  audioUrl: string;
  transcription?: string;
  status: 'new' | 'read' | 'archived';
  priority: 'normal' | 'urgent';
  assignedTo?: string;
}

// Voicemail actions
interface VoicemailActions {
  play(id: string): void;
  returnCall(id: string): void;
  forward(id: string, destination: string): void;
  archive(id: string): void;
  delete(id: string): void;
  markAsRead(id: string): void;
}
```

---

## Voicemail Drop

### Route Definition

```javascript
{
  path: '/voicemail-drop',
  name: 'VoicemailDrop',
  component: () => import('@/views/VoicemailDrop.vue'),
  meta: {
    requiresAuth: true,
    title: 'Voicemail Drop - Freedom Web',
    icon: 'mic'
  }
}
```

### Purpose

The Voicemail Drop view manages pre-recorded messages for outbound campaigns:

- **Recording Library**: Manage collection of pre-recorded messages
- **Recording Studio**: Create new voicemail recordings
- **Campaign Assignment**: Assign recordings to outbound campaigns
- **Analytics**: Track delivery and response rates
- **Templates**: Organize recordings by category or purpose

### Recording Management

```typescript
interface VoicemailDropRecording {
  id: string;
  name: string;
  description: string;
  audioUrl: string;
  duration: number;
  category: string;
  createdAt: Date;
  createdBy: string;
  usageCount: number;
  lastUsed?: Date;
}

// Recording creation workflow
interface RecordingWorkflow {
  startRecording(): void;
  stopRecording(): void;
  playbackRecording(): void;
  saveRecording(metadata: RecordingMetadata): Promise<VoicemailDropRecording>;
  uploadRecording(file: File, metadata: RecordingMetadata): Promise<VoicemailDropRecording>;
}
```

---

## Address Book

### Route Definition

```javascript
{
  path: '/address-book',
  name: 'AddressBook',
  component: () => import('@/views/AddressBook.vue'),
  meta: {
    requiresAuth: true,
    title: 'Address Book - Freedom Web',
    icon: 'users'
  }
}
```

### Purpose

The Address Book view provides comprehensive contact management:

- **Contact Directory**: Searchable list of all contacts
- **Contact Details**: View and edit contact information
- **Contact Creation**: Add new contacts manually or via import
- **Groups/Lists**: Organize contacts into logical groupings
- **Click-to-Call**: Initiate calls directly from contact records
- **Contact History**: View interaction history for each contact

### Data Model

```typescript
interface Contact {
  id: string;
  firstName: string;
  lastName: string;
  company?: string;
  title?: string;
  phoneNumbers: PhoneNumber[];
  emailAddresses: Email[];
  addresses: Address[];
  tags: string[];
  notes: string;
  createdAt: Date;
  updatedAt: Date;
  lastContactedAt?: Date;
}

interface PhoneNumber {
  type: 'work' | 'mobile' | 'home' | 'fax' | 'other';
  number: string;
  primary: boolean;
}
```

### Child Routes

```javascript
{
  path: '/address-book/:contactId',
  name: 'ContactDetail',
  component: () => import('@/views/ContactDetail.vue')
},
{
  path: '/address-book/new',
  name: 'NewContact',
  component: () => import('@/views/ContactForm.vue')
},
{
  path: '/address-book/:contactId/edit',
  name: 'EditContact',
  component: () => import('@/views/ContactForm.vue')
}
```

---

## Teams

### Route Definition

```javascript
{
  path: '/teams',
  name: 'Teams',
  component: () => import('@/views/Teams.vue'),
  meta: {
    requiresAuth: true,
    title: 'Teams - Freedom Web',
    icon: 'users-group'
  }
}
```

### Purpose

The Teams view facilitates team collaboration and communication:

- **Team Directory**: View team members and their current status
- **Real-time Presence**: See who is available, on call, or away
- **Internal Messaging**: Send quick messages to team members
- **Supervisor Tools**: Monitor team performance (for supervisors)
- **Transfer Shortcuts**: Quick warm/cold transfers to team members

### Team Features

```typescript
interface TeamMember {
  id: string;
  name: string;
  extension: string;
  email: string;
  role: 'agent' | 'supervisor' | 'admin';
  status: AgentStatus;
  currentCall?: ActiveCall;
  skills: string[];
  queues: string[];
}

type AgentStatus = 
  | 'available'
  | 'on_call'
  | 'wrap_up'
  | 'break'
  | 'meeting'
  | 'offline';

interface TeamView {
  members: TeamMember[];
  onlineCount: number;
  availableCount: number;
  inCallCount: number;
}
```

---

## Settings

### Route Definition

```javascript
{
  path: '/settings',
  name: 'Settings',
  component: () => import('@/views/Settings.vue'),
  meta: {
    requiresAuth: true,
    title: 'Settings - Freedom Web',
    icon: 'cog'
  }
}
```

### Purpose

The Settings view provides user and application configuration options:

- **Profile Settings**: Update personal information and preferences
- **Audio Settings**: Configure audio devices and volume levels
- **Notification Preferences**: Customize alert and notification behavior
- **Display Options**: Theme, language, and layout preferences
- **CTI Configuration**: Softphone and telephony integration settings
- **Keyboard Shortcuts**: View and customize hotkeys

### Settings Categories

```typescript
interface UserSettings {
  profile: ProfileSettings;
  audio: AudioSettings;
  notifications: NotificationSettings;
  display: DisplaySettings;
  cti: CTISettings;
  shortcuts: ShortcutSettings;
}

interface AudioSettings {
  inputDevice: string;
  outputDevice: string;
  ringDevice: string;
  inputVolume: number;
  outputVolume: number;
  ringVolume: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
}

interface CTISettings {
  autoAnswer: boolean;
  autoAnswerDelay: number;
  wrapUpTime: number;
  defaultDisposition: string;
  screenPopEnabled: boolean;
  recordingEnabled: boolean;
}
```

### Child Routes

```javascript
{
  path: '/settings/profile',
  name: 'ProfileSettings',
  component: () => import('@/views/settings/Profile.vue')
},
{
  path: '/settings/audio',
  name: 'AudioSettings',
  component: () => import('@/views/settings/Audio.vue')
},
{
  path: '/settings/notifications',
  name: 'NotificationSettings',
  component: () => import('@/views/settings/Notifications.vue')
},
{
  path: '/settings/cti',
  name: 'CTISettings',
  component: () => import('@/views/settings/CTI.vue')
}
```

---

## Route Constants

### Route Path Constants

```typescript
// src/constants/routes.ts

export const ROUTES = {
  DASHBOARD: '/',
  ACTIVE_CALLS: '/active-calls',
  WRAP_UPS: '/wrap-ups',
  ACTIVITIES: '/activities',
  CALL_LOGS: '/call-logs',
  VOICEMAILS: '/voicemails',
  VOICEMAIL_DROP: '/voicemail-drop',
  ADDRESS_BOOK: '/address-book',
  CONTACT_DETAIL: '/address-book/:contactId',
  CONTACT_NEW: '/address-book/new',
  CONTACT_EDIT: '/address-book/:contactId/edit',
  TEAMS: '/teams',
  SETTINGS: '/settings',
  SETTINGS_PROFILE: '/settings/profile',
  SETTINGS_AUDIO: '/settings/audio',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
  SETTINGS_CTI: '/settings/cti',
} as const;

export type RoutePath = typeof ROUTES[keyof typeof ROUTES];
```

### Route Names

```typescript
export const ROUTE_NAMES = {
  DASHBOARD: 'Dashboard',
  ACTIVE_CALLS: 'ActiveCalls',
  WRAP_UPS: 'WrapUps',
  ACTIVITIES: 'Activities',
  CALL_LOGS: 'CallLogs',
  VOICEMAILS: 'Voicemails',
  VOICEMAIL_DROP: 'VoicemailDrop',
  ADDRESS_BOOK: 'AddressBook',
  CONTACT_DETAIL: 'ContactDetail',
  CONTACT_NEW: 'NewContact',
  CONTACT_EDIT: 'EditContact',
  TEAMS: 'Teams',
  SETTINGS: 'Settings',
  SETTINGS_PROFILE: 'ProfileSettings',
  SETTINGS_AUDIO: 'AudioSettings',
  SETTINGS_NOTIFICATIONS: 'NotificationSettings',
  SETTINGS_CTI: 'CTISettings',
} as const;
```

### Navigation Guards

```typescript
// src/router/guards.ts

import { NavigationGuardNext, RouteLocationNormalized } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

export const authGuard = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } });
  } else {
    next();
  }
};

export const activeCallGuard = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const callStore = useCallStore();
  
  if (callStore.hasActiveCall && to.meta.confirmLeave) {
    const confirmed = window.confirm(
      'You have an active call. Are you sure you want to navigate away?'
    );
    if (!confirmed) {
      next(false);
      return;
    }
  }
  next();
};
```

### Route Utilities

```typescript
// src/utils/routing.ts

import { ROUTES } from '@/constants/routes';

export function buildContactDetailRoute(contactId: string): string {
  return ROUTES.CONTACT_DETAIL.replace(':contactId', contactId);
}

export function buildContactEditRoute(contactId: string): string {
  return ROUTES.CONTACT_EDIT.replace(':contactId', contactId);
}

export function buildCallLogsQuery(params: CallLogQueryParams): string {
  const searchParams = new URLSearchParams();
  
  if (params.startDate) searchParams.set('startDate', params.startDate);
  if (params.endDate) searchParams.set('endDate', params.endDate);
  if (params.direction) searchParams.set('direction', params.direction);
  if (params.page) searchParams.set('page', params.page.toString());
  
  return `${ROUTES.CALL_LOGS}?${searchParams.toString()}`;
}
```

---

## Common Patterns and Best Practices

### Route-Level Code Splitting

All feature routes implement lazy loading for optimal performance:

```javascript
// Good: Lazy loaded component
component: () => import('@/views/CallLogs.vue')

// Avoid: Eager loaded component for large views
import CallLogs from '@/views/CallLogs.vue';
component: CallLogs
```

### State Preservation

Routes that require state preservation use the `keepAlive` meta flag:

```javascript
meta: {
  keepAlive: true  // Preserves component state when navigating away
}
```

### Deep Linking Support

All list/search views support query parameters for deep linking:

```typescript
// Example: Sharing a filtered call log view
const shareableUrl = buildCallLogsQuery({
  startDate: '2024-01-01',
  endDate: '2024-01-31',
  direction: 'inbound'
});
```

### Error Handling

Implement route-level error boundaries for graceful degradation:

```javascript
{
  path: '/call-logs',
  name: 'CallLogs',
  component: () => import('@/views/CallLogs.vue'),
  meta: {
    errorComponent: () => import('@/views/errors/CallLogsError.vue')
  }
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Route not found (404) | Invalid path or missing route definition | Verify route exists in router configuration |
| Authentication redirect loop | Token expired during navigation | Clear auth state and redirect to login |
| State lost on navigation | Component not using keepAlive | Add `keepAlive: true` to route meta |
| Active call disconnected on route change | CTI bridge connection lost | Ensure CTI service persists across routes |

### Debug Mode

Enable route debugging in development:

```typescript
// src/router/index.ts
router.beforeEach((to, from) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Router] ${from.path} -> ${to.path}`);
  }
});
```