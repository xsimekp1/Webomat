import { Stack } from 'expo-router'
import { AuthProvider, useAuth } from '../context/AuthContext'

function RootLayoutNav() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return null // Or loading screen
  }

  return (
    <Stack screenOptions={{ headerShown: false }}>
      {isAuthenticated ? (
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      ) : (
        <Stack.Screen name="login" options={{ headerShown: false }} />
      )}
    </Stack>
  )
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootLayoutNav />
    </AuthProvider>
  )
}