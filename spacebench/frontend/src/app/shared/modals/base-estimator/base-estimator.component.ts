import {Component, EventEmitter, Output} from '@angular/core';

@Component({
    selector: 'app-base-estimator',
    standalone: true,
    templateUrl: './base-estimator.component.html',
    styleUrls: ['./base-estimator.component.scss'],
})
export class BaseEstimatorComponent {
    @Output() close = new EventEmitter<void>();


    downloadTemplate(): void {
        const a = document.createElement('a');
        a.href = 'assets/test-files/estimators/custom_estimator.py';
        a.download = 'custom_estimator.py';
        a.click();
    }

}
