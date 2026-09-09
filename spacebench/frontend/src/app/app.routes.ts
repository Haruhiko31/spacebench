import {Routes} from '@angular/router';
import {authGuard} from './service/auth.guard';

export const routes: Routes = [
    {path: '', redirectTo: 'login', pathMatch: 'full'},
    {path: 'login', loadComponent: () => import('./public/login/login.component').then(m => m.LoginComponent)},
    {
        path: 'dashboard',
        loadComponent: () => import('./admin/dashboard/dashboard.component').then(m => m.DashboardComponent),
        canActivate: [authGuard]
    },
    {
        path: 'new-analysis',
        loadComponent: () => import('./admin/new-analysis/new-analysis.component').then(m => m.NewAnalysisComponent),
        canActivate: [authGuard]
    },
    //{path: '**', loadComponent: () => import('./error/not-found/not-found.component').then(m => m.NotFoundComponent)},
];
