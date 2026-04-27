import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const ROUTE_PERMISSIONS: Record<string, string[]> = {
  '/admin': ['MANAGER', 'FINANCE', 'SUPER_ADMIN'],
  '/staff': ['STAFF', 'KITCHEN', 'MANAGER', 'SUPER_ADMIN'],
  '/dashboard': ['GUEST', 'STAFF', 'MANAGER', 'SUPER_ADMIN'],
};

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  
  // Exclude static files and api routes
  if (path.startsWith('/_next') || path.startsWith('/api') || path.includes('.')) {
    return NextResponse.next();
  }

  // Allow login pages
  if (path === '/admin/login' || path === '/staff/login' || path === '/login') {
    return NextResponse.next();
  }

  const token = request.cookies.get('access_token')?.value;

  const matchedPrefix = Object.keys(ROUTE_PERMISSIONS).find(prefix => path.startsWith(prefix));

  if (!matchedPrefix) {
    return NextResponse.next(); // Public route
  }

  if (!token) {
    if (path.startsWith('/admin')) return NextResponse.redirect(new URL('/admin/login', request.url));
    if (path.startsWith('/staff')) return NextResponse.redirect(new URL('/staff/login', request.url));
    return NextResponse.redirect(new URL('/login', request.url));
  }

  try {
    const secret = process.env.JWT_SECRET || 'dev-secret-key-change-in-production-64-chars-minimum-required!!';
    const { payload } = await jwtVerify(token, new TextEncoder().encode(secret));
    const userRoles = (payload.roles as string[]) || [];
    
    const allowed = ROUTE_PERMISSIONS[matchedPrefix];
    const hasAccess = userRoles.some(r => allowed.includes(r));

    if (!hasAccess) {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }
    
    return NextResponse.next();
  } catch (error) {
    if (path.startsWith('/admin')) return NextResponse.redirect(new URL('/admin/login?expired=1', request.url));
    if (path.startsWith('/staff')) return NextResponse.redirect(new URL('/staff/login?expired=1', request.url));
    return NextResponse.redirect(new URL('/login?expired=1', request.url));
  }
}
