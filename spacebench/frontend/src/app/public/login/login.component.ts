import {Component, ElementRef, OnDestroy, OnInit, ViewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {CommonModule} from '@angular/common';
import {AuthService} from '../../service/auth.service';

interface Star {
    x: number;
    y: number;
    radius: number;
    opacity: number;
    speed: number;
}

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [FormsModule, CommonModule],
    templateUrl: './login.component.html',
    styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit, OnDestroy {
    @ViewChild('sky', {static: true}) skyRef!: ElementRef<HTMLCanvasElement>;

    username = '';
    password = '';
    error = '';
    loading = false;

    private stars: Star[] = [];
    private animationId = 0;

    constructor(
        private auth: AuthService,
        private router: Router
    ) {}

    ngOnInit(): void {
        this.initStars();
        this.animate();
    }

    ngOnDestroy(): void {
        cancelAnimationFrame(this.animationId);
    }

    private initStars(): void {
        const canvas = this.skyRef.nativeElement;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        this.stars = Array.from({length: 180}, () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 1.2 + 0.2,
            opacity: Math.random(),
            speed: Math.random() * 0.004 + 0.001,
        }));
    }

    private animate(): void {
        const canvas = this.skyRef.nativeElement;
        const ctx = canvas.getContext('2d')!;

        const loop = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (const star of this.stars) {
                star.opacity += star.speed;
                if (star.opacity > 1 || star.opacity < 0) star.speed *= -1;

                ctx.beginPath();
                ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 255, 255, ' + star.opacity + ')';
                ctx.fill();
            }

            this.animationId = requestAnimationFrame(loop);
        };

        this.animationId = requestAnimationFrame(loop);
    }

    submit(): void {
        if (!this.auth.connect(this.username, this.password)) {
            this.error = 'Identifiants incorrects.';
            return;
        }

        this.loading = true;
        setTimeout(() => this.router.navigate(['/dashboard']), 900);
    }
}
