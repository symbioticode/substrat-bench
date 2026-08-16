"""Émission d'événements AGNOS v2 pour l'observabilité du banc.

Cette trace décrit l'état opérationnel. Elle ne remplace jamais le registre
d'inférence ni les artefacts scientifiques du protocole.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


STATUSES = {"en_attente", "en_cours", "succès", "échec"}
LIFECYCLES = {"actif", "termine"}
HEALTH_STATES = {"operationnel", "erreur", "indetermine"}
RESULT_STATES = {"stable", "divergence", "indetermine"}


class AgnosEventWriter:
    """Producteur append-only minimal du contrat AGNOS v2."""

    def __init__(self, path: Path, run_id: str):
        self.path = Path(path)
        self.run_id = run_id
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        *,
        agent_id: str,
        status: str,
        task: str,
        detail: str,
        lifecycle: str,
        health: str,
        result: str = "indetermine",
        pipeline: Optional[str] = None,
        cycle: Optional[str] = None,
        repetition: Optional[int] = None,
        artifact_ref: Optional[str] = None,
        **extensions: Any,
    ) -> dict[str, Any]:
        if status not in STATUSES:
            raise ValueError(f"statut AGNOS invalide: {status}")
        if lifecycle not in LIFECYCLES:
            raise ValueError(f"cycle_vie AGNOS invalide: {lifecycle}")
        if health not in HEALTH_STATES:
            raise ValueError(f"sante AGNOS invalide: {health}")
        if result not in RESULT_STATES:
            raise ValueError(f"resultat AGNOS invalide: {result}")

        event: dict[str, Any] = {
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "statut": status,
            "tâche": task,
            "détail": detail,
            "cycle_vie": lifecycle,
            "sante": health,
            "resultat": result,
            "run_id": self.run_id,
        }
        optional = {
            "pipeline": pipeline,
            "cycle": cycle,
            "repetition": repetition,
            "artifact_ref": artifact_ref,
            **extensions,
        }
        event.update({key: value for key, value in optional.items() if value is not None})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
        return event

