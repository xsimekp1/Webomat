'use client'

export default function HelpPage() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">❓ Nápověda</h1>

      <div className="space-y-8">
        {/* Přehled platformy */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Co je Webomat</h2>
          <p className="text-gray-700 mb-4">
            Webomat je platforma pro:
          </p>
          <ul className="list-disc list-inside space-y-1 text-gray-600">
            <li><strong>sběr leadů / kontaktů</strong> (firmy, které typicky nemají web, ale mají dobré hodnocení)</li>
            <li><strong>řízení obchodního procesu</strong> (CRM: kontakt → deal/projekt → follow-up)</li>
            <li><strong>automatizovanou tvorbu webu</strong> (generování webové stránky pomocí AI)</li>
            <li><strong>správu verzí webu</strong> pod jedním projektem</li>
            <li>a do budoucna <strong>fakturaci a provize</strong> (pro klienty i obchodníky)</li>
          </ul>
        </section>

        {/* Workflow */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Jak vypadá tok práce</h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium mb-2">A) Získání kontaktu</h3>
              <p className="text-gray-600">
                Kontakt může přijít z více zdrojů:
              </p>
              <ul className="list-disc list-inside mt-2 text-gray-600">
                <li><strong>automaticky</strong> (Webomat skript hledá podniky z Google Places a filtruje dle ratingu / recenzí)</li>
                <li><strong>ručně</strong> (někdo zadá kontakt v UI)</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">B) CRM kvalifikace</h3>
              <p className="text-gray-600">
                Na kontaktu držíme identifikační info, stav v CRM, plánování, vlastníka, poznámky.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">C) Deal / Projekt</h3>
              <p className="text-gray-600">
                Z kontaktu vznikne Deal (obchodní případ) a klient může mít více projektů.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">D) Zadání webu a generování</h3>
              <p className="text-gray-600">
                Zadání obsahuje text, inspirace, assety. Generování vytvoří verzi webu.
              </p>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Často kladené otázky</h2>

          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium mb-2">Proč některé kontakty nevidím?</h3>
              <ul className="list-disc list-inside text-gray-600">
                <li>můžeš mít filtr (status, owner)</li>
                <li>nebo kontakt patří jinému obchodníkovi</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">Jak poznám, že je něco testovací?</h3>
              <p className="text-gray-600">
                test záznamy označit štítkem "TEST"
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium mb-2">Proč mi nejde vygenerovat web?</h3>
              <ul className="list-disc list-inside text-gray-600">
                <li>můžeš být reviewer → generování zablokované</li>
                <li>nebo není vyplněné zadání</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}