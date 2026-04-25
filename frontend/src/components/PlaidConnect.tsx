import { useEffect, useState } from "react";
import {
  createPlaidLinkToken,
  exchangePlaidPublicToken,
  syncPlaidTransactions,
} from "../api";

declare global {
  interface Window {
    Plaid?: {
      create: (config: {
        token: string;
        onSuccess: (publicToken: string, metadata: PlaidSuccessMetadata) => void;
        onExit?: (error: { error_message?: string } | null) => void;
      }) => { open: () => void; destroy: () => void };
    };
  }
}

type PlaidSuccessMetadata = {
  institution?: {
    institution_id?: string | null;
    name?: string | null;
  } | null;
};

type PlaidConnectProps = {
  phoneNumber: string;
  onSynced: () => void;
};

let plaidScriptPromise: Promise<void> | null = null;

function loadPlaidScript() {
  if (window.Plaid) {
    return Promise.resolve();
  }

  if (!plaidScriptPromise) {
    plaidScriptPromise = new Promise((resolve, reject) => {
      const existingScript = document.querySelector<HTMLScriptElement>(
        'script[src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"]',
      );
      if (existingScript) {
        existingScript.addEventListener("load", () => resolve(), { once: true });
        existingScript.addEventListener("error", () => reject(new Error("Plaid Link failed to load.")), {
          once: true,
        });
        return;
      }

      const script = document.createElement("script");
      script.src = "https://cdn.plaid.com/link/v2/stable/link-initialize.js";
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Plaid Link failed to load."));
      document.head.appendChild(script);
    });
  }

  return plaidScriptPromise;
}

function PlaidConnect({ phoneNumber, onSynced }: PlaidConnectProps) {
  const [status, setStatus] = useState(
    "Click Connect bank to open Plaid. Bank login happens in the Plaid popup.",
  );
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    void loadPlaidScript().catch(() => {
      setStatus("Plaid Link could not load. Check your connection and try again.");
    });
  }, []);

  async function handleConnectClick() {
    setIsBusy(true);
    setStatus("Preparing Plaid Link...");

    try {
      await loadPlaidScript();
      const linkToken = await createPlaidLinkToken(phoneNumber);
      const handler = window.Plaid?.create({
        token: linkToken,
        onSuccess: (publicToken, metadata) => {
          setStatus("Importing transactions...");
          void exchangePlaidPublicToken(phoneNumber, publicToken, metadata.institution ?? undefined)
            .then((result) => {
              setStatus(
                `Imported ${result.sync.added} transactions from ${
                  result.institution_name ?? "your bank"
                }.`,
              );
              onSynced();
            })
            .catch((error) => {
              setStatus(error instanceof Error ? error.message : "Plaid import failed.");
            })
            .finally(() => setIsBusy(false));
        },
        onExit: (error) => {
          setStatus(error?.error_message ?? "Plaid connection closed.");
          setIsBusy(false);
        },
      });

      if (!handler) {
        throw new Error("Plaid Link is unavailable.");
      }

      handler.open();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to start Plaid Link.";
      setStatus(
        message === "Not Found"
          ? "Plaid routes are not live yet. Restart the backend, then click Connect bank again."
          : message,
      );
      setIsBusy(false);
    }
  }

  async function handleSyncClick() {
    setIsBusy(true);
    setStatus("Checking Plaid for new transactions...");

    try {
      const result = await syncPlaidTransactions(phoneNumber);
      setStatus(`Synced ${result.sync.added} new and ${result.sync.modified} updated transactions.`);
      onSynced();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Plaid sync failed.";
      setStatus(
        message === "Not Found"
          ? "No bank is connected yet. Click Connect bank first, then run Sync."
          : message,
      );
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="panel plaid-card" aria-label="Plaid bank connection">
      <div className="card-title-row">
        <div>
          <p className="section-label">bank connection</p>
          <h2>Plaid import</h2>
          <p className="plaid-copy">Use Plaid Link to choose a bank and enter Sandbox credentials.</p>
        </div>
        <div className="plaid-actions">
          <button className="secondary-action compact-action" type="button" onClick={handleSyncClick} disabled={isBusy}>
            Sync
          </button>
          <button className="primary-action compact-action" type="button" onClick={handleConnectClick} disabled={isBusy}>
            Connect bank
          </button>
        </div>
      </div>
      <p className="status-banner">{status}</p>
    </section>
  );
}

export default PlaidConnect;
