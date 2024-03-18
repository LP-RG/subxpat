module top (a,b,r);
input [5:0] a,b;
output [5:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
