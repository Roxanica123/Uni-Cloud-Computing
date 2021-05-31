import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { UserRoles } from './models/UserRoles';
import { AuthComponent } from './pages/auth/auth.component';

import { IndicationsPageComponent } from './pages/indications-page/indications-page.component';
import { PendingProblemDetailsPageComponent } from './pages/pending-problem-details-page/pending-problem-details-page.component';
import { PendingProblemsPageComponent } from './pages/pending-problems-page/pending-problems-page.component';
import { PremiumPageComponent } from './pages/premium-page/premium-page.component';
import { ProblemDetailsPageComponent } from './pages/problem-details-page/problem-details-page.component';
import { ProblemsPageComponent } from './pages/problems-page/problems-page.component';
import { ProblemsUploadPageComponent } from './pages/problems-upload-page/problems-upload-page.component';
import { SolutionPageComponent } from './pages/solution-page/solution-page.component';
import { SubmissionPageComponent } from './pages/submission-page/submission-page.component';
import { SubmissionsPageComponent } from './pages/submissions-page/submissions-page.component';
import { SubmitPageComponent } from './pages/submit-page/submit-page.component';
import { AuthGuardService } from './services/auth-guard.service';
import { AuthNotGuardService } from './services/auth-not-guard.service';

const routes: Routes = [
  {
    path: 'problems',
    component: ProblemsPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'pending',
    component: PendingProblemsPageComponent,
    canActivate: [AuthGuardService],
    data: { roles: [UserRoles.ADMIN, UserRoles.MODERATOR] }
  },
  {
    path: 'upload',
    component: ProblemsUploadPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'problems/:id',
    component: ProblemDetailsPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'pending/:id',
    component: PendingProblemDetailsPageComponent,
    canActivate: [AuthGuardService],
    data: { roles: [UserRoles.ADMIN, UserRoles.MODERATOR] }
  },
  {
    path: 'problems/:id/submit',
    component: SubmitPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: ':case/:id/solution',
    component: SolutionPageComponent,
    canActivate: [AuthGuardService],
    data: { roles: [UserRoles.ADMIN, UserRoles.MODERATOR, UserRoles.PREMIUM] }
  },
  {
    path: ':case/:id/indications',
    component: IndicationsPageComponent,
    canActivate: [AuthGuardService],
    data: { roles: [UserRoles.ADMIN, UserRoles.MODERATOR, UserRoles.PREMIUM] }
  },
  {
    path: 'submissions',
    component: SubmissionsPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'submission/:id',
    component: SubmissionPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'premium',
    component: PremiumPageComponent,
    canActivate: [AuthGuardService],
  },
  {
    path: 'auth',
    component: AuthComponent,
    canActivate: [AuthNotGuardService],
  },

  {
    path: '',
    redirectTo: '/problems',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: '/problems',
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule],
})
export class AppRoutingModule { }
