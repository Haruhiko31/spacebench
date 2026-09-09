import {Injectable, NgZone} from '@angular/core';
import { Subject, Observable } from 'rxjs';
import {TestEvent} from "../interfaces/tests.interface";
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class TestsService {

  private eventSource: EventSource | null = null;

  constructor(private zone: NgZone) {}

  runTests(target: string = 'backend'): Observable<TestEvent> {
    const subject = new Subject<TestEvent>();

    this.stop();

    if(target === 'backend'){
      this.eventSource = new EventSource(`${environment.apiUrl}/api/tests/run`);
    }else{
      this.eventSource = new EventSource(`${environment.podEngineUrl}/pod/tests/run`);
    }


    this.eventSource.onmessage = (event) => {
      this.zone.run(() => {
        const data: TestEvent = JSON.parse(event.data);
        subject.next(data);

        if (data.type === 'done') {
          this.stop();
          subject.complete();
        }
      });
    };

    this.eventSource.onerror = () => {
      this.zone.run(() => {
        this.stop();
        subject.error('Connection lost');
      });
    };

    return subject.asObservable();
  }

  stop(): void {
    this.eventSource?.close();
    this.eventSource = null;
  }
}
