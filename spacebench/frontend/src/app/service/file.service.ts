import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {environment} from '../../environments/environment';

@Injectable({providedIn: 'root'})
export class FileService {
    constructor(private http: HttpClient) {
    }

    upload(file: File): Observable<{ id: string }> {
        const form = new FormData();
        form.append('file', file);
        return this.http.post<{ id: string }>(environment.apiUrl + '/api/files/upload', form);
    }


    download(fileId: string): Observable<Blob>{
        return this.http.get(environment.apiUrl + '/api/files/' + fileId + '/download', {
            responseType: 'blob'
        });
    }

    downloadBulk(fileIds: string[]): Observable<Blob> {
        return this.http.post(environment.apiUrl + '/api/files/bulk/download', fileIds, {
            responseType: 'blob'
        });
    }

}
