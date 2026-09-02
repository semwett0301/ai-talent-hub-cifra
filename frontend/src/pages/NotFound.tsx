import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <section>
      <h1>404</h1>
      <p>
        Page not found. <Link to="/">Back to dashboard</Link>
      </p>
    </section>
  )
}

export default NotFound
