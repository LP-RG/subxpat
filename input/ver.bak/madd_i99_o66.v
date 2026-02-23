module madd_i99_o66 (a, b, c, r);
input [32:0] a,b,c;
output [65:0] r;

assign r = (a * b) + c;

endmodule
