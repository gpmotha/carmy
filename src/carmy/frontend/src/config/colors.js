/**
 * Carmy Style Guide Colors
 * Fine-dining aesthetic, minimal and clean
 */

export const colors = {
  // Primary - Carmy Blue
  carmyBlue: '#1C2A39',
  carmyBlueDark: '#141D28',
  carmyBlueLight: '#2C3E50',

  // Background - Kitchen White
  kitchenWhite: '#F5F5F2',
  white: '#FFFFFF',
  warmWhite: '#FAFAF8',

  // Accent - Herb Green (success)
  herbGreen: '#4E6E58',
  herbGreenLight: '#E8F0EA',

  // Accent - Tomato Red (danger)
  tomatoRed: '#B23A48',
  tomatoRedLight: '#F8E8EA',

  // Neutrals
  stone: '#6B7280',
  stoneLight: '#9CA3AF',
  stoneDark: '#374151',

  // Borders
  border: '#E5E5E0',
  borderLight: '#F0F0EB',
};

// Semantic color assignments
export const semanticColors = {
  // Backgrounds
  background: colors.kitchenWhite,
  cardBackground: colors.white,

  // Text
  textPrimary: colors.carmyBlue,
  textSecondary: colors.stone,
  textMuted: colors.stoneLight,

  // States
  success: colors.herbGreen,
  successLight: colors.herbGreenLight,
  danger: colors.tomatoRed,
  dangerLight: colors.tomatoRedLight,

  // Interactive
  primary: colors.carmyBlue,
  primaryDark: colors.carmyBlueDark,
  primaryLight: colors.carmyBlueLight,

  // Borders
  border: colors.border,
  borderMuted: colors.borderLight,
};

// Shadows - subtle, refined
export const shadows = {
  sm: '0 1px 3px rgba(0,0,0,0.06)',
  md: '0 2px 6px rgba(0,0,0,0.08)',
  lg: '0 4px 12px rgba(0,0,0,0.10)',
  card: '0 2px 6px rgba(0,0,0,0.08)',
  hover: '0 4px 12px rgba(0,0,0,0.12)',
};

// Gradients - minimal
export const gradients = {
  primary: `linear-gradient(135deg, ${colors.carmyBlue} 0%, ${colors.carmyBlueDark} 100%)`,
  fresh: `linear-gradient(135deg, ${colors.herbGreenLight} 0%, ${colors.herbGreen}15 100%)`,
  leftover: `linear-gradient(135deg, ${colors.kitchenWhite} 0%, ${colors.border} 100%)`,
  header: `linear-gradient(180deg, ${colors.white} 0%, ${colors.kitchenWhite} 100%)`,
};

export default colors;
