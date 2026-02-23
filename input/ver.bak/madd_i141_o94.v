module madd_i141_o94 (a, b, c, r);
input [46:0] a,b,c;
output [93:0] r;

assign r = (a * b) + c;

endmodule
