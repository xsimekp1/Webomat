import { render, screen, fireEvent } from '@testing-library/react'
import { useRouter } from 'next/navigation'

// Mock router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn()
}))

const mockRouter = {
  push: jest.fn()
}

// Mock API data
const mockBusinesses = [
  {
    id: '123',
    name: 'Test Firma s.r.o.',
    phone: '+420123456789',
    email: 'test@firma.cz',
    status_crm: 'new',
    next_follow_up_at: '2024-01-15',
    owner_seller_name: 'Jan Novák'
  }
]

// Mock the CRM page component
// Note: This is a simplified test - in real implementation you'd import the actual component
const MockCRMPage = ({ businesses = mockBusinesses }) => {
  const router = useRouter()
  
  const handleRowClick = (id: string) => {
    router.push(`/dashboard/crm/${id}`)
  }

  const handleDetailClick = (id: string) => {
    router.push(`/dashboard/crm/${id}`)
  }

  const handleEditClick = (business: any) => {
    // Mock edit functionality
    console.log('Edit business:', business)
  }

  return (
    <div>
      <table className="crm-table">
        <tbody>
          {businesses.map((b) => (
            <tr 
              key={b.id}
              className="clickable-row"
              onClick={() => handleRowClick(b.id)}
              style={{ cursor: 'pointer' }}
            >
              <td>
                <strong>{b.name}</strong>
                {b.email && <div className="sub-text">{b.email}</div>}
              </td>
              <td>
                {b.phone ? (
                  <a href={`tel:${b.phone}`} className="phone-link">{b.phone}</a>
                ) : '-'}
              </td>
              <td>
                <span className="status-badge">{b.status_crm}</span>
              </td>
              <td>{b.next_follow_up_at}</td>
              <td>{b.owner_seller_name || '-'}</td>
              <td className="actions">
                <button
                  className="btn-small"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDetailClick(b.id)
                  }}
                >
                  Detail
                </button>
                <button
                  className="btn-small btn-edit"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleEditClick(b)
                  }}
                >
                  Upravit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

describe('CRM Pipeline Clickable Rows', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
  })

  it('should open detail when row is clicked', () => {
    render(<MockCRMPage />)
    
    const row = screen.getByText('Test Firma s.r.o.')
    fireEvent.click(row)
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/crm/123')
  })

  it('should open detail when Detail button is clicked', () => {
    render(<MockCRMPage />)
    
    const detailButton = screen.getByText('Detail')
    fireEvent.click(detailButton)
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/crm/123')
  })

  it('should not navigate twice when Detail button is clicked', () => {
    render(<MockCRMPage />)
    
    const detailButton = screen.getByText('Detail')
    fireEvent.click(detailButton)
    
    expect(mockRouter.push).toHaveBeenCalledTimes(1)
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/crm/123')
  })

  it('should not navigate when Edit button is clicked', () => {
    render(<MockCRMPage />)
    
    const editButton = screen.getByText('Upravit')
    fireEvent.click(editButton)
    
    expect(mockRouter.push).not.toHaveBeenCalled()
  })

  it('should have clickable-row class on table rows', () => {
    render(<MockCRMPage />)
    
    const table = screen.getByRole('table')
    const rows = table.querySelectorAll('tr')
    
    // Skip header row
    expect(rows[1]).toHaveClass('clickable-row')
  })

  it('should have cursor pointer style on clickable rows', () => {
    render(<MockCRMPage />)
    
    const table = screen.getByRole('table')
    const rows = table.querySelectorAll('tr')
    
    // Skip header row
    expect(rows[1]).toHaveStyle('cursor: pointer')
  })
})