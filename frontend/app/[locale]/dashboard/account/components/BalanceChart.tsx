'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, Tooltip, Legend, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Area, AreaChart } from 'recharts'
import ApiClient from '../../../../lib/api'
import { useAuth } from '../../../../context/AuthContext'

interface BalanceData {
  date: string
  earned: number
  paid_out: number
  adjustments: number
  balance: number
}

interface ChartDataPoint {
  date: string
  earned: number
  balance: number
  adjustments?: number
}

export const BalanceChart = () => {
  const { user } = useAuth()
  const [data, setData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'3m' | '6m' | '12m'>('3m')

  const fetchData = async () => {
    if (!user) return

    try {
      setLoading(true)
      const ledgerResponse = await ApiClient.getSellerAccountLedger({
        range: timeRange
      })

      // Transform data for chart - pokládáme na availability filter
      const chartData: ChartDataPoint[] = []
      let runningBalance = 0

      // Process in reverse chronological order
      const sortedTransactions = (ledgerResponse.ledger_entries || [])
        .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        .filter(entry => entry.type !== 'payout_reserved') // Exclude pending transactions

      for (const entry of sortedTransactions) {
        const date = new Date(entry.created_at).toISOString().split('T')[0]
        
        // Calculate running balance
        if (entry.type === 'commission_earned') {
          runningBalance += entry.amount
        } else if (entry.type === 'admin_adjustment') {
          runningBalance += entry.amount
        } else if (entry.type === 'payout_paid') {
          runningBalance += Math.abs(entry.amount) // Payouts are stored as negative
        }

        // Only show dates with balance changes for sales users
        if (user.role === 'sales' && entry.type === 'commission_earned') {
          if (chartData.length === 0 || chartData[chartData.length - 1].date !== date) {
            chartData.push({
              date,
              earned: runningBalance - Math.abs(entry.amount || 0),
              balance: runningBalance,
              adjustments: 0
            })
          }
        } else if (user.role === 'admin') {
          chartData.push({
            date,
              earned: entry.type === 'commission_earned' ? entry.amount : 0,
              balance: runningBalance,
              adjustments: entry.type === 'admin_adjustment' ? entry.amount : 0
          })
        }
      }

      setData(chartData)
    } catch (error) {
      console.error('Error fetching balance data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [timeRange, user?.role])

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('cs-CZ', {
      style: 'currency',
      currency: 'CZK'
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('cs-CZ', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="loading-chart">
        <div className="spinner"></div>
        <p>Načítám graf...</p>
      </div>
    )
  }

  return (
    <div className="balance-chart">
      <div className="chart-header">
        <h3>Přehled pohybů na účtu</h3>
        
        <div className="chart-controls">
          <label>
            Období:
            <select 
              value={timeRange} 
              onChange={(e) => setTimeRange(e.target.value as '3m' | '6m' | '12m')}
            >
              <option value="3m">Poslední 3 měsíce</option>
              <option value="6m">Poslední 6 měsíců</option>
              <option value="12m">Poslední rok</option>
            </select>
          </label>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            tick={{ fontSize: 12 }}
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            tickFormatter={formatAmount}
            domain={[0, 'auto']}
          />
          <Tooltip 
            content={({ active, payload }: any) => {
              if (active && payload) {
                return (
                  <div className="chart-tooltip">
                    <p><strong>{formatDate(payload[0]?.payload?.date || '')}</strong></p>
                    <p>Vyděláno: {formatAmount(payload[0]?.value || 0)}</p>
                    <p>Zůstatek: {formatAmount(payload[1]?.value || 0)}</p>
                    {payload[2]?.value !== undefined && (
                      <p>Adjustementy: {formatAmount(payload[2]?.value)}</p>
                    )}
                  </div>
                )
              }
              return null
            }}
          />
          <Legend 
            verticalAlign="top" 
            height={36}
            iconType="rect"
            formatter={(value, entry) => (
              <span style={{ color: entry.color }}>
                {value === 'earned' && 'Vyděláno'}
                {value === 'balance' && 'Zůstatek'}
                {value === 'adjustments' && 'Adjustementy'}
              </span>
            )}
          />
          <Line 
            type="monotone" 
            dataKey="earned" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 2 }}
          />
          <Line 
            type="monotone" 
            dataKey="balance" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={{ fill: '#8884d8', strokeWidth: 2 }}
          />
          {user.role === 'admin' && (
            <Line 
              type="monotone" 
              dataKey="adjustments" 
              stroke="#ffa726" 
              strokeWidth={1}
              strokeDasharray="5 5"
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <div className="chart-summary">
        {data.length > 0 && (
          <>
            <div className="summary-item">
              <strong>Poslední zůstatek:</strong>
              <span>{formatAmount(data[data.length - 1]?.balance || 0)}</span>
            </div>
            
            {user.role === 'sales' && (
              <div className="summary-item">
                <strong>Celkem vybráno:</strong>
                <span>{formatAmount(
                  data.reduce((sum, item) => sum + item.earned, 0)
                )}</span>
              </div>
            )}
            
            {user.role === 'admin' && (
              <div className="summary-item">
                <strong>Celkové adjustementy:</strong>
                <span>{formatAmount(
                  data.reduce((sum, item) => sum + (item.adjustments || 0), 0)
                )}</span>
              </div>
            )}
          </>
        )}
      </div>

      <style jsx>{`
        .balance-chart {
          padding: 20px;
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .chart-header h3 {
          margin: 0;
        }

        .chart-controls {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .chart-controls label {
          font-weight: 500;
        }

        .chart-controls select {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
        }

        .loading-chart {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 200px;
        }

        .chart-summary {
          margin-top: 20px;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .summary-item {
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          text-align: center;
        }

        .summary-item strong {
          display: block;
          margin-bottom: 5px;
          color: #374151;
        }

        .chart-tooltip {
          background: rgba(0, 0, 0, 0.9);
          border: 1px solid #ccc;
          border-radius: 8px;
          padding: 12px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .chart-tooltip p {
          margin: 0;
          line-height: 1.4;
        }

        .chart-tooltip strong {
          display: block;
          margin-bottom: 4px;
          color: #333;
        }
      `}</style>
    </div>
  )
}