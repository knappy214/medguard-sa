# Avatar Component

A reusable avatar component that follows DaisyUI 5 best practices and provides consistent avatar styling across the MedGuard SA application.

## Features

- **DaisyUI 5 Compliant**: Uses proper DaisyUI avatar structure with `mask mask-circle`
- **Responsive Sizing**: Multiple size options from xs to 2xl
- **Smart Initials**: Automatically generates initials from name or email
- **Image Support**: Displays user images when available
- **Fallback Handling**: Shows initials when no image is provided
- **Status Indicators**: Optional online/offline status indicators
- **Accessibility**: Proper alt text and semantic markup

## Usage

### Basic Usage

```vue
<template>
  <!-- With image -->
  <Avatar 
    src="/path/to/image.jpg"
    alt="User profile picture"
    name="John Doe"
  />
  
  <!-- With initials only -->
  <Avatar 
    name="John Doe"
    size="lg"
  />
</template>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | `string` | `undefined` | Image URL for the avatar |
| `alt` | `string` | `'User avatar'` | Alt text for the image |
| `name` | `string` | `''` | User's full name for generating initials |
| `email` | `string` | `''` | User's email (fallback for initials) |
| `size` | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl' \| '2xl'` | `'md'` | Size of the avatar |
| `status` | `'online' \| 'offline'` | `undefined` | Online/offline status indicator |

### Size Options

- `xs`: 32px (w-8 h-8)
- `sm`: 40px (w-10 h-10)
- `md`: 48px (w-12 h-12) - Default
- `lg`: 64px (w-16 h-16)
- `xl`: 80px (w-20 h-20)
- `2xl`: 96px (w-24 h-24)

### Examples

```vue
<!-- Navigation avatar -->
<Avatar 
  :name="user.name"
  :email="user.email"
  size="sm"
  alt="User avatar"
/>

<!-- Profile page avatar -->
<Avatar 
  :src="avatarUrl"
  :name="profileData.first_name + ' ' + profileData.last_name"
  size="2xl"
  alt="Profile picture"
/>

<!-- With online status -->
<Avatar 
  name="John Doe"
  status="online"
  size="md"
/>
```

## DaisyUI Integration

This component uses the following DaisyUI classes:
- `avatar` - Main avatar container
- `avatar-online` / `avatar-offline` - Status indicators
- `mask mask-circle` - Circular mask for images and initials
- `bg-primary` / `text-primary-content` - Primary color scheme for initials

## Accessibility

- Proper `alt` attributes for images
- Semantic HTML structure
- High contrast text for initials
- Responsive design for different screen sizes

## Testing

The component includes comprehensive tests covering:
- Image rendering
- Initials generation
- Size variations
- Status indicators
- Fallback behavior

Run tests with: `npm run test Avatar.test.ts` 