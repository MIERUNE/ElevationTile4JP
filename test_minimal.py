# Fichier : plugin_dir/test_suite/test_minimal.py

import unittest

# L'initialisation doit se faire AVANT tout autre import de qgis.core
from qgis.testing import start_app

start_app()

from qgis.core import Qgis


class MinimalTest(unittest.TestCase):
    """
    Une suite de tests minimale pour valider l'environnement.
    """

    def test_qgis_initialization(self):
        """
        Teste si QGIS est initialisé et si la version est accessible.
        """
        print("Vérification de la version de QGIS...")
        version = Qgis.version()
        self.assertIsInstance(
            version, str, "La version de QGIS devrait être une chaîne de caractères."
        )
        self.assertTrue(
            len(version) > 0,
            "La chaîne de la version de QGIS ne devrait pas être vide.",
        )
        print(f"Test minimal réussi avec la version de QGIS : {version}")


if __name__ == "__main__":
    unittest.main()
