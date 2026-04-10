import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Simple auth middleware - checks for admin session
export function middleware(request: NextRequest) {
  const isAdminRoute = request.nextUrl.pathname.startsWith('/admin')
  const isLoginPage = request.nextUrl.pathname === '/admin/login'
  
  if (isAdminRoute && !isLoginPage) {
    const adminToken = request.cookies.get('luxura_admin_token')
    
    if (!adminToken) {
      return NextResponse.redirect(new URL('/admin/login', request.url))
    }
  }
  
  return NextResponse.next()
}

export const config = {
  matcher: '/admin/:path*',
}
