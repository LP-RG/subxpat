module madd_i381_o254 (a, b, c, r);
input [126:0] a,b,c;
output [253:0] r;

assign r = (a * b) + c;

endmodule
