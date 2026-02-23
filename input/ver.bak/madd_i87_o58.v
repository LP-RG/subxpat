module madd_i87_o58 (a, b, c, r);
input [28:0] a,b,c;
output [57:0] r;

assign r = (a * b) + c;

endmodule
