import {Injectable} from '@angular/core';

const UTILISATEUR_PAR_DEFAUT = {nom: 'usertest', motDePasse: 'CHANGE_ME___kKbvtu3LbI6yYQltgWdz'};

@Injectable({providedIn: 'root'})
export class AuthService {

    connect(nom: string, motDePasse: string): boolean {
        if (nom === UTILISATEUR_PAR_DEFAUT.nom && motDePasse === UTILISATEUR_PAR_DEFAUT.motDePasse) {
            sessionStorage.setItem('connecte', 'true');
            return true;
        }
        return false;
    }

    disconnect(): void {
        sessionStorage.removeItem('connecte');
    }

    isConnected(): boolean {
        return sessionStorage.getItem('connecte') === 'true';
    }
}
