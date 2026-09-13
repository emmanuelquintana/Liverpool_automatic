import assert from "node:assert/strict";
import { createSession, verifySession } from "./session.ts";

const secret = "a-test-secret-that-is-long-enough";
const token = await createSession("emmanuel", secret);
assert.equal(await verifySession(token, secret), true);
assert.equal(await verifySession(`${token}x`, secret), false);
assert.equal(await verifySession(undefined, secret), false);
console.log("session signing: ok");
