module mul_i180_o180 (a, b, r);
input [89:0] a,b;
output [179:0] r;

assign r = a * b;

endmodule
