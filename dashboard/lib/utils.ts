export function parseUtcTimestamp(ts: string): Date {
  // If the string has no timezone info (no 'Z' and no +/-HH:MM offset),
  // treat it as UTC by appending 'Z'.
  const hasTimezone = /[Zz]|[+-]\d{2}:?\d{2}$/.test(ts);
  return new Date(hasTimezone ? ts : ts + 'Z');
}
