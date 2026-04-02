module madd_i327_o218 (a, b, c, r);
input [108:0] a,b,c;
output [217:0] r;

assign r = (a * b) + c;

endmodule
