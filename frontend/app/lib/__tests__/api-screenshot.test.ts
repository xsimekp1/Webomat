import ApiClient from '../api'

// Mock axios
jest.mock('axios')
const mockedAxios = require('axios') as any

describe('Screenshot API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Mock auth headers
    mockedAxios.defaults = {
      headers: {
        common: {
          Authorization: 'Bearer test-token'
        }
      }
    }
  })

  it('should send viewport parameter instead of type', async () => {
    const mockResponse = { data: { screenshot_url: 'test.jpg' } }
    mockedAxios.post.mockResolvedValue(mockResponse)

    await ApiClient.screenshotTestWebsite('<html>test</html>', 'thumbnail')

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining('/website/screenshot-test'),
      { html_content: '<html>test</html>', viewport: 'thumbnail' },
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Authorization: expect.any(String)
        })
      })
    )
  })

  it('should send screenshot type correctly', async () => {
    const mockResponse = { data: { screenshot_url: 'test.jpg' } }
    mockedAxios.post.mockResolvedValue(mockResponse)

    await ApiClient.screenshotTestWebsite('<html>test</html>', 'screenshot')

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining('/website/screenshot-test'),
      { html_content: '<html>test</html>', viewport: 'screenshot' },
      expect.any(Object)
    )
  })

  it('should handle API errors gracefully', async () => {
    const mockError = new Error('API Error')
    mockError.response = { status: 500, data: { message: 'Server error' } }
    mockedAxios.post.mockRejectedValue(mockError)

    await expect(ApiClient.screenshotTestWebsite('<html>test</html>', 'thumbnail'))
      .rejects.toThrow('API Error')
  })
})