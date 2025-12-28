export default function Footer() {
  return (
    <footer className="text-center py-6 text-sm text-stone border-t border-lavender-light/30 mt-8">
      <p>
        Carmy &copy; {new Date().getFullYear()} &bull;{' '}
        <span className="text-lavender">Meal Planning, Elevated</span>
      </p>
    </footer>
  )
}
