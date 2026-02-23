module madd_i345_o230 (a, b, c, r);
input [114:0] a,b,c;
output [229:0] r;

assign r = (a * b) + c;

endmodule
