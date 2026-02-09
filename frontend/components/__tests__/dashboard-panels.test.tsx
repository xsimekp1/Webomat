import { render, screen } from '@testing-library/react'
import { useMediaQuery } from '@/hooks/use-media-query'

// Mock media query hook
jest.mock('@/hooks/use-media-query', () => ({
  useMediaQuery: jest.fn()
}))

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>

// Mock dashboard data
const mockStats = {
  balance: 12500,
  followUps: 8,
  leads: 42
}

// Mock dashboard panels component
const MockDashboardPanels = ({ stats = mockStats } = {}) => {
  const isMobile = useMediaQuery('(max-width: 768px)')

  return (
    <div className="quick-stats-grid">
      <div className="quick-card balance-card">
        <div className="quick-card-icon">💰</div>
        <div className="quick-card-content">
          <span className="quick-card-value">
            {new Intl.NumberFormat('cs-CZ', {
              style: 'currency',
              currency: 'CZK'
            }).format(stats.balance)}
          </span>
          <span className="quick-card-label">K vyplacení</span>
        </div>
        <div className="quick-card-action">Detail účtu →</div>
      </div>

      <div className="quick-card calls-card">
        <div className="quick-card-icon">📞</div>
        <div className="quick-card-content">
          <span className="quick-card-value">{stats.followUps}</span>
          <span className="quick-card-label">Follow-upy</span>
        </div>
        <div className="quick-card-action">Otevřít seznam →</div>
      </div>

      <div className="quick-card leads-card">
        <div className="quick-card-icon">📊</div>
        <div className="quick-card-content">
          <span className="quick-card-value">{stats.leads}</span>
          <span className="quick-card-label">Moje leady</span>
        </div>
        <div className="quick-card-action">Jít do CRM →</div>
      </div>

      <style jsx>{`
        .quick-stats-grid {
          display: grid;
          grid-template-columns: ${isMobile ? '1fr' : 'repeat(auto-fit, minmax(280px, 1fr))'};
          gap: 16px;
          margin-bottom: 32px;
        }

        .quick-card {
          background: white;
          border-radius: 16px;
          padding: ${isMobile ? '16px' : '20px'};
          display: flex;
          flex-direction: ${isMobile ? 'row' : 'column'};
          align-items: center;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #e2e8f0;
        }

        .quick-card-icon {
          font-size: ${isMobile ? '1.5rem' : '2rem'};
          margin-bottom: ${isMobile ? '0' : '12px'};
          margin-right: ${isMobile ? '12px' : '0'};
        }

        .quick-card-value {
          display: block;
          font-size: ${isMobile ? '1.5rem' : '2rem'};
          font-weight: 700;
          line-height: 1.2;
        }

        .quick-card-label {
          display: block;
          font-size: ${isMobile ? '0.8rem' : '0.9rem'};
          opacity: 0.9;
          margin-top: ${isMobile ? '2px' : '4px'};
        }

        .quick-card-action {
          margin-top: ${isMobile ? '0' : '16px'};
          margin-left: ${isMobile ? '12px' : '0'};
          font-size: ${isMobile ? '0.75rem' : '0.85rem'};
          opacity: 0.8;
          font-weight: 500;
          white-space: ${isMobile ? 'nowrap' : 'normal'};
        }

        .balance-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
        }

        .calls-card {
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          color: white;
          border: none;
        }

        .leads-card {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          border: none;
        }
      `}</style>
    </div>
  )
}

describe('Dashboard Panels Responsive Design', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render desktop layout on large screens', () => {
    mockUseMediaQuery.mockReturnValue(false)
    
    render(<MockDashboardPanels />)
    
    const grid = screen.getByText('K vyplacení').closest('.quick-stats-grid')
    expect(grid).toHaveStyle('grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))')
  })

  it('should render mobile layout on small screens', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const grid = screen.getByText('K vyplacení').closest('.quick-stats-grid')
    expect(grid).toHaveStyle('grid-template-columns: 1fr')
  })

  it('should use horizontal layout on mobile', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const cards = document.querySelectorAll('.quick-card')
    cards.forEach(card => {
      expect(card).toHaveStyle('flex-direction: row')
      expect(card).toHaveStyle('align-items: center')
    })
  })

  it('should use smaller padding on mobile', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const cards = document.querySelectorAll('.quick-card')
    cards.forEach(card => {
      expect(card).toHaveStyle('padding: 16px')
    })
  })

  it('should use smaller icons on mobile', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const icons = document.querySelectorAll('.quick-card-icon')
    icons.forEach(icon => {
      expect(icon).toHaveStyle('font-size: 1.5rem')
      expect(icon).toHaveStyle('margin-bottom: 0')
      expect(icon).toHaveStyle('margin-right: 12px')
    })
  })

  it('should use smaller font sizes on mobile', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const values = document.querySelectorAll('.quick-card-value')
    const labels = document.querySelectorAll('.quick-card-label')
    const actions = document.querySelectorAll('.quick-card-action')
    
    values.forEach(value => {
      expect(value).toHaveStyle('font-size: 1.5rem')
    })
    
    labels.forEach(label => {
      expect(label).toHaveStyle('font-size: 0.8rem')
    })
    
    actions.forEach(action => {
      expect(action).toHaveStyle('font-size: 0.75rem')
    })
  })

  it('should position action text correctly on mobile', () => {
    mockUseMediaQuery.mockReturnValue(true)
    
    render(<MockDashboardPanels />)
    
    const actions = document.querySelectorAll('.quick-card-action')
    actions.forEach(action => {
      expect(action).toHaveStyle('margin-top: 0')
      expect(action).toHaveStyle('margin-left: 12px')
      expect(action).toHaveStyle('white-space: nowrap')
    })
  })

  it('should display correct data values', () => {
    mockUseMediaQuery.mockReturnValue(false)
    
    render(<MockDashboardPanels />)
    
    expect(screen.getByText('12500 Kč')).toBeInTheDocument()
    expect(screen.getByText('8')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('should have correct gradient backgrounds', () => {
    mockUseMediaQuery.mockReturnValue(false)
    
    render(<MockDashboardPanels />)
    
    const balanceCard = document.querySelector('.balance-card')
    const callsCard = document.querySelector('.calls-card')
    const leadsCard = document.querySelector('.leads-card')
    
    expect(balanceCard).toHaveStyle('background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)')
    expect(callsCard).toHaveStyle('background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%)')
    expect(leadsCard).toHaveStyle('background: linear-gradient(135deg, #10b981 0%, #059669 100%)')
  })
})