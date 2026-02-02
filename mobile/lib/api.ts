// Mobile-specific API client wrapper
import AsyncStorage from '@react-native-async-storage/async-storage'
import { ApiClient } from '@/shared/api'

// Override platform-specific functions for React Native
Object.assign(ApiClient, {
  getAuthHeaders: () => {
    // This will be set by the auth context
    return {}
  },
  getStoredToken: async () => {
    return await AsyncStorage.getItem('token')
  },
  setStoredToken: async (token: string | null) => {
    if (token) {
      await AsyncStorage.setItem('token', token)
    } else {
      await AsyncStorage.removeItem('token')
    }
  },
})

// Export the configured ApiClient
export { ApiClient }
export default ApiClient