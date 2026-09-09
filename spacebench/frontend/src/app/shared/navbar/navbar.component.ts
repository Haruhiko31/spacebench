import {Component, HostListener} from '@angular/core';
import {Router, RouterLink} from '@angular/router';
import {CommonModule} from '@angular/common';
import {AuthService} from '../../service/auth.service';
import {environment} from '../../../environments/environment';
import {LucideAngularModule} from "lucide-angular";
import {TooltipModule} from "primeng/tooltip";
import {UnitTestsRunComponent} from "../modals/unit-tests-run/unit-tests-run.component";

@Component({
    selector: 'app-navbar',
    standalone: true,
    imports: [CommonModule, RouterLink, LucideAngularModule, TooltipModule, UnitTestsRunComponent],
    templateUrl: './navbar.component.html',
    styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent {
    menuDocsOpen = false;
    apiUrl = environment.apiUrl;
    docsUrl = environment.docsUrl;
    isDevMode = !environment.production;
    modalVisible = false;

    constructor(private auth: AuthService, private router: Router) {
    }

    disconnect(): void {
        this.auth.disconnect();
        this.router.navigate(['/login']);
    }

    openTestModal(): void {
        this.modalVisible = !this.modalVisible;
    }
}
