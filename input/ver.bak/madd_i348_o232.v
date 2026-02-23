module madd_i348_o232 (a, b, c, r);
input [115:0] a,b,c;
output [231:0] r;

assign r = (a * b) + c;

endmodule
