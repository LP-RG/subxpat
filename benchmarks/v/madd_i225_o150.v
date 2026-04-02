module madd_i225_o150 (a, b, c, r);
input [74:0] a,b,c;
output [149:0] r;

assign r = (a * b) + c;

endmodule
