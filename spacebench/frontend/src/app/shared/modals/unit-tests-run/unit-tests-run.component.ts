import {Component, EventEmitter, Input, Output, OnDestroy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {DialogModule} from 'primeng/dialog';
import {LucideAngularModule} from 'lucide-angular';
import {TestResult} from "../../../interfaces/tests.interface";
import {Subscription} from "rxjs";
import {TestsService} from "../../../service/test_runner.service";
import {concat, defer} from 'rxjs';


@Component({
    selector: 'app-unit-tests-run',
    standalone: true,
    imports: [CommonModule, DialogModule, LucideAngularModule],
    templateUrl: './unit-tests-run.component.html',
    styleUrl: './unit-tests-run.component.scss',
})
export class UnitTestsRunComponent {
    @Input() visible = false;
    @Output() visibleChange = new EventEmitter<boolean>();

    tests: TestResult[] = []
    running = false;
    private subscription: Subscription | null = null

    constructor(private testsService: TestsService) {
    }

    get passCount(): number {
        return this.tests.filter(t => t.status === 'PASSED').length
    }

    get failCount(): number {
        return this.tests.filter(t => t.status === 'FAILED').length
    }

    get errorCount(): number{
        return this.tests.filter(t => t.status === 'ERROR').length
    }

    runTests(): void {

        if (this.running) return;

        this.tests = [];
        this.running = true;

        this.subscription = concat(
            defer(() => this.testsService.runTests('backend')),
            defer(() => this.testsService.runTests('pod-engine')),
        ).subscribe({
            next: (event) => {
                if (event.type === 'result') {
                    this.tests = [...this.tests, {
                        name: event.name!,
                        file: event.file!,
                        status: event.status as any,
                        expanded: false,
                    }];
                }
                if (event.type === 'failure') {
                    this.tests = this.tests.map(
                        t => t.name === event.name ? {...t, log: event.log!} : t
                    );
                }
            },
            error: () => this.running = false,
            complete: () => this.running = false,
        });
    }


    close(): void {
        this.subscription?.unsubscribe();
        this.testsService.stop();
        this.visible = false;
        this.visibleChange.emit(false);
    }

    ngOnDestroy(): void {
        this.subscription?.unsubscribe();
        this.testsService.stop();
    }

}
