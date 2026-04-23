module madd_i108_o72 (a, b, c, r);
input [35:0] a,b,c;
output [71:0] r;

assign r = (a * b) + c;

endmodule
