import assert from "node:assert/strict";
import { carrierName, classifyTrackingHtml, trackingUrl } from "./shipment-control.ts";

assert.equal(classifyTrackingHtml('<p class="fontColorCurrentProcess">La guía ha sido generada; aún no es depositado</p>').status, "no_movement");
assert.equal(classifyTrackingHtml('<strong class="fontColorCurrentProcess">En tránsito</strong>').status, "in_transit");
assert.equal(classifyTrackingHtml('<div class="fontColorCurrentProcess">ENTREGADO</div>').status, "delivered");
assert.equal(classifyTrackingHtml("<script>const labels=['Delivered','In transit']</script>", "UPS", "1Z6751V50439609622").status, "manual_review");
assert.equal(classifyTrackingHtml('{"trackingNumber":"1Z6751V50439609622","statusDescription":"Delivered"}', "UPS", "1Z6751V50439609622").status, "delivered");

const carrier = carrierName("1Z6751V50439609622");
assert.equal(carrier, "UPS");
assert.match(trackingUrl(carrier, "1Z6751V50439609622"), /tracknum=1Z6751V50439609622/);

console.log("tracking parser: ok");
