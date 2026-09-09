import {bootstrapApplication} from '@angular/platform-browser';
import {appConfig} from './app/app.config';
import {AppComponent} from './app/app.component';
import {importProvidersFrom} from '@angular/core';
import {provideHttpClient} from '@angular/common/http';
import {
    LucideAngularModule,
    Home,
    SearchCheck,
    ArrowDownUp,
    ArrowDown10,
    ArrowUp10,
    Download,
    BugPlay,
    Loader,
    Play,
    Minus,
    Check,
    X,
    ChevronUp,
    ChevronDown,
    Microscope,
    ChartNoAxesColumnIncreasing,
    Scale,
    Loader2,
    CheckCheck,
    Info
} from 'lucide-angular';
import {providePrimeNG} from 'primeng/config';
import Aura from '@primeuix/themes/aura';

bootstrapApplication(AppComponent, {
    ...appConfig,
    providers: [
        importProvidersFrom(
            LucideAngularModule.pick({
                Home,
                SearchCheck,
                ArrowDownUp,
                ArrowDown10,
                ArrowUp10,
                Download,
                BugPlay,
                Loader,
                Play,
                Minus,
                Check,
                X,
                ChevronUp,
                ChevronDown,
                Microscope,
                ChartNoAxesColumnIncreasing,
                Scale,
                Loader2,
                CheckCheck,
                Info
            }),
        ),
        providePrimeNG({
            theme: {
                preset: Aura,
                options: {darkModeSelector: '.p-dark'}
            }
        }),

        provideHttpClient(),
        ...appConfig.providers
    ]
}).catch(err => console.error(err));