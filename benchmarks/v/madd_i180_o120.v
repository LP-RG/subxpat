module madd_i180_o120 (a, b, c, r);
input [59:0] a,b,c;
output [119:0] r;

assign r = (a * b) + c;

endmodule
