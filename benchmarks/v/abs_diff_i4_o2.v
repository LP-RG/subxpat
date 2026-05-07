module top (a,b,r);
input [1:0] a,b;
output [1:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
