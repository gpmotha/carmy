/**
 * Carmy Theme Configurations
 * - Provance: Original lavender luxury aesthetic
 * - Bear: Clean, minimal fine-dining aesthetic (Carmy Blue)
 */

export const themes = {
  provance: {
    name: 'Provance',
    colors: {
      // Primary - Lavender
      primary: '#9B7BB8',
      primaryDark: '#7B5B98',
      primaryLight: '#E8E0F0',

      // Secondary - Sage Green
      secondary: '#9CAF88',
      secondaryLight: '#D4E4C8',

      // Accents
      accent: '#F5E6C8',
      accentDark: '#D4A574',
      wheat: '#F5E6C8',
      terracotta: '#D4A574',
      olive: '#6B7B5C',

      // Backgrounds
      background: '#FBF9F6',
      cardBackground: '#FFFCF7',
      white: '#FFFFFF',
      cream: '#FBF9F6',

      // Text
      textPrimary: '#7B5B98',
      textSecondary: '#8B7E74',
      textMuted: '#6B7B5C',

      // States
      success: '#9CAF88',
      successLight: '#D4E4C8',
      danger: '#D4A574',
      dangerLight: '#F5E6C8',

      // Borders
      border: '#E8E0F0',
      borderLight: '#F0EBF5',

      // Swimlane colors (original)
      breakfast: '#F5E6C8',
      lunch: '#9CAF88',
      dinner: '#9B7BB8',
    },
    shadows: {
      sm: '0 2px 8px rgba(0,0,0,0.04)',
      md: '0 4px 20px rgba(0,0,0,0.06)',
      lg: '0 8px 40px rgba(0,0,0,0.08)',
      card: '0 4px 20px rgba(0,0,0,0.06)',
      hover: '0 12px 40px rgba(155,123,184,0.2)',
      primary: '0 8px 24px rgba(155,123,184,0.3)',
    },
    gradients: {
      primary: 'linear-gradient(135deg, #9B7BB8 0%, #7B5B98 100%)',
      fresh: 'linear-gradient(135deg, #D4E4C8 0%, rgba(156,175,136,0.3) 100%)',
      leftover: 'linear-gradient(135deg, #F5E6C8 0%, rgba(212,165,116,0.2) 100%)',
      header: 'radial-gradient(ellipse at top, rgba(155,123,184,0.4) 0%, transparent 70%)',
    },
    borderRadius: {
      sm: '12px',
      md: '16px',
      lg: '20px',
    },
    // Use Playfair Display for Provance
    fontSerif: "'Playfair Display', 'Didot', Georgia, serif",
  },

  bear: {
    name: 'Bear',
    colors: {
      // Primary - Carmy Blue
      primary: '#1C2A39',
      primaryDark: '#141D28',
      primaryLight: '#2C3E50',

      // Secondary - Herb Green
      secondary: '#4E6E58',
      secondaryLight: '#E8F0EA',

      // Accents
      accent: '#B23A48',
      accentDark: '#8B2D38',
      wheat: '#F5F5F2',
      terracotta: '#B23A48',
      olive: '#4E6E58',

      // Backgrounds
      background: '#F5F5F2',
      cardBackground: '#FFFFFF',
      white: '#FFFFFF',
      cream: '#F5F5F2',

      // Text
      textPrimary: '#1C2A39',
      textSecondary: '#6B7280',
      textMuted: '#9CA3AF',

      // States
      success: '#4E6E58',
      successLight: '#E8F0EA',
      danger: '#B23A48',
      dangerLight: '#F8E8EA',

      // Borders
      border: '#E5E5E0',
      borderLight: '#F0F0EB',

      // Swimlane colors (Bear - more subtle)
      breakfast: '#F5F5F2',
      lunch: '#F5F5F2',
      dinner: '#F5F5F2',
    },
    shadows: {
      sm: '0 1px 3px rgba(0,0,0,0.06)',
      md: '0 2px 6px rgba(0,0,0,0.08)',
      lg: '0 4px 12px rgba(0,0,0,0.10)',
      card: '0 2px 6px rgba(0,0,0,0.08)',
      hover: '0 4px 12px rgba(0,0,0,0.12)',
      primary: '0 2px 6px rgba(0,0,0,0.08)',
    },
    gradients: {
      primary: 'linear-gradient(135deg, #1C2A39 0%, #141D28 100%)',
      fresh: 'linear-gradient(135deg, #E8F0EA 0%, rgba(78,110,88,0.15) 100%)',
      leftover: 'linear-gradient(135deg, #F5F5F2 0%, #E5E5E0 100%)',
      header: 'linear-gradient(180deg, #FFFFFF 0%, #F5F5F2 100%)',
    },
    borderRadius: {
      sm: '6px',
      md: '8px',
      lg: '8px',
    },
    // Use Cormorant Garamond for Bear
    fontSerif: "'Cormorant Garamond', Georgia, serif",
  },
}

export const defaultTheme = 'bear'

export default themes
