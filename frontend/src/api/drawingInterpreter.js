export async function interpretDrawingText(text) {
  const response = await fetch('/api/interpret-drawing', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })

  if (!response.ok) {
    throw new Error(`Drawing interpretation request failed: ${response.status}`)
  }

  const data = await response.json()

  if (!data.success || !data.drawing) {
    throw new Error('Drawing interpretation failed')
  }

  return data.drawing
}
