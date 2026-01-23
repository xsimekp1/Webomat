import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Linking,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { StatusBar } from 'expo-status-bar'
import { Ionicons } from '@expo/vector-icons'
import AsyncStorage from '@react-native-async-storage/async-storage'

import { ApiClient } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'
import type { CRMStats, TodayTask, SellerDashboard, User } from '@/shared/types'

export default function DashboardScreen() {
  const { user, logout } = useAuth()
  const [stats, setStats] = useState<CRMStats | null>(null)
  const [todayTasks, setTodayTasks] = useState<TodayTask[]>([])
  const [sellerDashboard, setSellerDashboard] = useState<SellerDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const loadData = async () => {
    try {
      const [statsData, tasksData, sellerData] = await Promise.all([
        ApiClient.getCRMStats(),
        ApiClient.getTodayTasks(),
        ApiClient.getSellerDashboard().catch(() => null), // Optional for sales users
      ])

      setStats(statsData)
      setTodayTasks(tasksData.tasks)
      setSellerDashboard(sellerData)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
      Alert.alert('Chyba', 'Nepodařilo se načíst data dashboardu')
    }
  }

  useEffect(() => {
    loadData().finally(() => setLoading(false))
  }, [])

  const onRefresh = async () => {
    setRefreshing(true)
    await loadData()
    setRefreshing(false)
  }

  const makeCall = (phone: string) => {
    const url = `tel:${phone}`
    Linking.openURL(url)
  }

  const markTaskDone = (taskId: string) => {
    Alert.alert(
      'Označit jako hotovo',
      'Opravdu jste firmu kontaktovali?',
      [
        { text: 'Zrušit', style: 'cancel' },
        {
          text: 'Hotovo',
          onPress: () => {
            // Remove task from local state
            setTodayTasks(prev => prev.filter(task => task.id !== taskId))
          }
        }
      ]
    )
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('cs-CZ', {
      style: 'currency',
      currency: 'CZK',
    }).format(amount)
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loading}>
          <Text>Načítám...</Text>
        </View>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" backgroundColor="#667eea" />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>Webomat CRM</Text>
          <Text style={styles.headerSubtitle}>
            {user ? `Ahoj, ${user.name}!` : 'Načítám...'}
          </Text>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Stats Cards */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Ionicons name="business" size={24} color="#3b82f6" />
            <Text style={styles.statValue}>{stats?.total_leads ?? '--'}</Text>
            <Text style={styles.statLabel}>Leadů</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="call" size={24} color="#eab308" />
            <Text style={styles.statValue}>{stats?.follow_ups_today ?? '--'}</Text>
            <Text style={styles.statLabel}>Dnes volat</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="briefcase" size={24} color="#f97316" />
            <Text style={styles.statValue}>{sellerDashboard?.pending_projects_amount ? formatCurrency(sellerDashboard.pending_projects_amount) : '--'}</Text>
            <Text style={styles.statLabel}>Aktivní projekty</Text>
          </View>

          <View style={styles.statCard}>
            <Ionicons name="wallet" size={24} color="#22c55e" />
            <Text style={styles.statValue}>
              {sellerDashboard?.available_balance ? formatCurrency(sellerDashboard.available_balance) : '--'}
            </Text>
            <Text style={styles.statLabel}>Provize</Text>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rychlé akce</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="call" size={20} color="#fff" />
              <Text style={styles.actionButtonText}>Volat teď</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="add-circle" size={20} color="#fff" />
              <Text style={styles.actionButtonText}>Nová aktivita</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton}>
              <Ionicons name="briefcase" size={20} color="#fff" />
              <Text style={styles.actionButtonText}>Mé projekty</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Today's Tasks */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Dnešní úkoly ({todayTasks.length})</Text>

          {todayTasks.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="checkmark-circle" size={48} color="#22c55e" />
              <Text style={styles.emptyStateText}>Žádné úkoly na dnešek!</Text>
            </View>
          ) : (
            todayTasks.map((task) => (
              <View key={task.id} style={styles.taskCard}>
                <View style={styles.taskContent}>
                  <Text style={styles.taskTitle}>{task.business_name}</Text>
                  {task.phone && (
                    <Text style={styles.taskPhone}>{task.phone}</Text>
                  )}
                  <Text style={styles.taskStatus}>
                    Status: {task.status_crm}
                  </Text>
                </View>

                <View style={styles.taskActions}>
                  {task.phone && (
                    <TouchableOpacity
                      style={[styles.taskAction, styles.callAction]}
                      onPress={() => makeCall(task.phone!)}
                    >
                      <Ionicons name="call" size={16} color="#fff" />
                    </TouchableOpacity>
                  )}

                  <TouchableOpacity
                    style={[styles.taskAction, styles.doneAction]}
                    onPress={() => markTaskDone(task.id)}
                  >
                    <Ionicons name="checkmark" size={16} color="#fff" />
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#667eea',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#e0e7ff',
  },
  scrollView: {
    flex: 1,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
    textAlign: 'center',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: 16,
  },
  actionsGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#667eea',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    marginTop: 8,
    textAlign: 'center',
  },
  emptyState: {
    alignItems: 'center',
    padding: 32,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 16,
  },
  taskCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  taskContent: {
    flex: 1,
  },
  taskTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 4,
  },
  taskPhone: {
    fontSize: 14,
    color: '#667eea',
    marginBottom: 2,
  },
  taskStatus: {
    fontSize: 12,
    color: '#6b7280',
  },
  taskActions: {
    flexDirection: 'row',
    gap: 8,
  },
  taskAction: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  callAction: {
    backgroundColor: '#22c55e',
  },
  doneAction: {
    backgroundColor: '#667eea',
  },
})