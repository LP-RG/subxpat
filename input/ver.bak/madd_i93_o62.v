module madd_i93_o62 (a, b, c, r);
input [30:0] a,b,c;
output [61:0] r;

assign r = (a * b) + c;

endmodule
